use std::panic::catch_unwind;
use std::slice;
use crate::{IdentityKeypair, VolatileSession, initiate_handshake, complete_handshake};

pub extern "C" fn vnp_identity_generate() -> *mut IdentityKeypair {
    let result = catch_unwind(|| {
        let keypair = IdentityKeypair::generate();
        Box::into_raw(Box::new(keypair))
    });
    result.unwrap_or(std::ptr::null_mut())
}

pub extern "C" fn vnp_identity_free(ptr: *mut IdentityKeypair) {
    if !ptr.is_null() {
        let _ = catch_unwind(|| {
            unsafe { Box::from_raw(ptr) }; 
        });
    }
}

pub extern "C" fn vnp_initiate_handshake(
    identity_ptr: *mut IdentityKeypair,
    out_public_bytes: *mut u8,
    out_signature_bytes: *mut u8,
) -> libc::c_int {
    if identity_ptr.is_null() || out_public_bytes.is_null() || out_signature_bytes.is_null() {
        return -1;
    }

    let result = catch_unwind(|| {
        let identity = unsafe { &*identity_ptr };
        let (_, pub_bytes, sig_bytes) = initiate_handshake(identity);

        unsafe {
            std::ptr::copy_nonoverlapping(pub_bytes.as_ptr(), out_public_bytes, 32);
            std::ptr::copy_nonoverlapping(sig_bytes.as_ptr(), out_signature_bytes, 64);
        }
        0
    });
    result.unwrap_or(-2)
}

pub extern "C" fn vnp_session_create(
    identity_ptr: *mut IdentityKeypair,
    peer_pub: *const u8,
    peer_sig: *const u8,
    trusted_identity: *const u8,
    is_initiator: libc::c_int,
) -> *mut VolatileSession {
    if identity_ptr.is_null() || peer_pub.is_null() || peer_sig.is_null() || trusted_identity.is_null() {
        return std::ptr::null_mut();
    }

    let result = catch_unwind(|| {
        let mut p_pub = [0u8; 32];
        let mut p_sig = [0u8; 64];
        let mut t_id = [0u8; 32];

        unsafe {
            std::ptr::copy_nonoverlapping(peer_pub, p_pub.as_mut_ptr(), 32);
            std::ptr::copy_nonoverlapping(peer_sig, p_sig.as_mut_ptr(), 64);
            std::ptr::copy_nonoverlapping(trusted_identity, t_id.as_mut_ptr(), 32);
        }

        let mut rng = rand_core::OsRng;
        let ephemeral_private = x25519_dalek::EphemeralSecret::random_from_rng(&mut rng);

        match complete_handshake(ephemeral_private, p_pub, p_sig, t_id, is_initiator != 0) {
            Ok(session) => Box::into_raw(Box::new(session)),
            Err(_) => std::ptr::null_mut(),
        }
    });
    result.unwrap_or(std::ptr::null_mut())
}

pub extern "C" fn vnp_session_decrypt(
    session_ptr: *mut VolatileSession,
    buf_ptr: *mut u8,
    buf_size: libc::size_t,
) -> libc::c_int {
    if session_ptr.is_null() || buf_ptr.is_null() || buf_size == 0 {
        return -1;
    }

    let result = catch_unwind(|| {
        let session = unsafe { &mut *session_ptr };
        let slice = unsafe { slice::from_raw_parts_mut(buf_ptr, buf_size as usize) };

        match session.process_layer_decrypt(slice) {
            Ok(_) => 0,
            Err(_) => -2,
        }
    });
    result.unwrap_or(-3)
}

pub extern "C" fn vnp_session_free(ptr: *mut VolatileSession) {
    if !ptr.is_null() {
        let _ = catch_unwind(|| {
            unsafe { Box::from_raw(ptr) };
        });
    }
}
