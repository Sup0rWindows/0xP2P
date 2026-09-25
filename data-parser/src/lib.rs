use ed25519_dalek::{Signature, Signer, Verifier, SigningKey, VerifyingKey};
use x25519_dalek::{EphemeralSecret, PublicKey as XPublicKey};
use ring::aead::{LessSafeKey, UnboundKey, CHACHA20_POLY1305, Nonce, BoundKey, Aad};
use hkdf::Hkdf;
use sha2::Sha256;
use zeroize::{Zeroize, ZeroizeOnDrop};
use rand_core::RngCore;
pub mod ffi;


#[derive(Zeroize, ZeroizeOnDrop)]
pub struct VolatileSession {
    tx_key: [u8; 32],
    rx_key: [u8; 32],
    tx_nonce_counter: u64,
    rx_nonce_counter: u64,
}

pub struct IdentityKeypair {
    pub signing_key: SigningKey,
}

impl IdentityKeypair {
    pub fn generate() -> Self {
        let mut entropy = [0u8; 32];
        let mut rng = rand_core::OsRng;
        rng.fill_bytes(&mut entropy);
        let signing_key = SigningKey::from_bytes(&entropy);
        Self { signing_key }
    }
}

pub fn initiate_handshake(identity: &IdentityKeypair) -> (EphemeralSecret, [u8; 32], [u8; 64]) {
    let mut rng = rand_core::OsRng;
    let ephemeral_private = EphemeralSecret::random_from_rng(&mut rng);
    let ephemeral_public = XPublicKey::from(&ephemeral_private);
    let public_bytes = ephemeral_public.to_bytes();
    let signature = identity.signing_key.sign(&public_bytes).to_bytes();
    (ephemeral_private, public_bytes, signature)
}

pub fn complete_handshake(
    ephemeral_private: EphemeralSecret,
    peer_ephemeral_bytes: [u8; 32],
    peer_signature_bytes: [u8; 64],
    trusted_peer_identity_bytes: [u8; 32],
    is_initiator: bool,
) -> Result<VolatileSession, &'static str> {
    let peer_identity = VerifyingKey::from_bytes(&trusted_peer_identity_bytes)
        .map_err(|_| "INVALID_IDENTITY_FORMAT")?;
    
    let signature = Signature::from_bytes(&peer_signature_bytes);
    peer_identity.verify(&peer_ephemeral_bytes, &signature)
        .map_err(|_| "AUTHENTICATION_FAILURE_MITM_DETECTED")?;

    let peer_ephemeral_public = XPublicKey::from(peer_ephemeral_bytes);
    let shared_secret = ephemeral_private.diffie_hellman(&peer_ephemeral_public);
    let secret_bytes = shared_secret.as_bytes();

    let hk = Hkdf::<Sha256>::new(None, secret_bytes);
    let mut okm = [0u8; 64];
    hk.expand(b"VNP_VOLATILE_STREAM_SALT", &mut okm)
        .map_err(|_| "KEY_DERIVATION_CRITICAL_ERROR")?;

    let mut key_material_a = [0u8; 32];
    let mut key_material_b = [0u8; 32];
    key_material_a.copy_from_slice(&okm[0..32]);
    key_material_b.copy_from_slice(&okm[32..64]);

    okm.zeroize();

    let (tx_key, rx_key) = if is_initiator {
        (key_material_a, key_material_b)
    } else {
        (key_material_b, key_material_a)
    };

    Ok(VolatileSession {
        tx_key,
        rx_key,
        tx_nonce_counter: 0,
        rx_nonce_counter: 0,
    })
}

impl VolatileSession {
    pub fn process_layer_encrypt(&mut self, payload: &mut Vec<u8>) -> Result<(), &'static str> {
        let unbound_key = UnboundKey::new(&CHACHA20_POLY1305, &self.tx_key)
            .map_err(|_| "CIPHER_INIT_FAILED")?;
        let encryption_key = LessSafeKey::new(unbound_key);

        let mut nonce_bytes = [0u8; 12];
        nonce_bytes[4..12].copy_from_slice(&self.tx_nonce_counter.to_be_bytes());
        let nonce = Nonce::assume_unique_attributes(nonce_bytes);
        
        self.tx_nonce_counter += 1;

        encryption_key.seal_in_place_append_tag(nonce, Aad::empty(), payload)
            .map_err(|_| "ENCRYPTION_CRITICAL_FAILURE")?;

        Ok(())
    }

    pub fn process_layer_decrypt<'a>(&mut self, ciphertext: &'a mut [u8]) -> Result<&'a mut [u8], &'static str> {
        let unbound_key = UnboundKey::new(&CHACHA20_POLY1305, &self.rx_key)
            .map_err(|_| "CIPHER_INIT_FAILED")?;
        let decryption_key = LessSafeKey::new(unbound_key);

        let mut nonce_bytes = [0u8; 12];
        nonce_bytes[4..12].copy_from_slice(&self.rx_nonce_counter.to_be_bytes());
        let nonce = Nonce::assume_unique_attributes(nonce_bytes);

        self.rx_nonce_counter += 1;

        let decrypted_buffer = decryption_key.open_in_place(nonce, Aad::empty(), ciphertext)
            .map_err(|_| "DECRYPTION_INTEGRITY_VIOLATION")?;

        Ok(decrypted_buffer)
    }
}
