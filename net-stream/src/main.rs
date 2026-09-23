use futures::StreamExt;
use libp2p::{
    dcutr, identity,
    identify,
    kad::{store::MemoryStore, Kademlia, KademliaEvent},
    noise,
    relay::client as relay_client,
    swarm::{NetworkBehaviour, SwarmEvent},
    tcp, quic, yamux, Multiaddr, PeerId, Swarm,
};
use std::error::Error;
use std::time::Duration;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use zeroize::{Zeroize, ZeroizeOnDrop};

#[derive(NetworkBehaviour)]
#[behaviour(out_event = "CommsEvent")]
struct VolatileBehaviour {
    kademlia: Kademlia<MemoryStore>,
    identify: identify::Behaviour,
    relay_client: relay_client::Behaviour,
    dcutr: dcutr::Behaviour,
}

#[derive(Debug)]
enum CommsEvent {
    Kademlia(KademliaEvent),
    Identify(identify::Event),
    RelayClient(relay_client::Event),
    Dcutr(dcutr::Event),
}

impl From<KademliaEvent> for CommsEvent {
    fn from(event: KademliaEvent) -> Self {
        CommsEvent::Kademlia(event)
    }
}

impl From<identify::Event> for CommsEvent {
    fn from(event: identify::Event) -> Self {
        CommsEvent::Identify(event)
    }
}

impl From<relay_client::Event> for CommsEvent {
    fn from(event: relay_client::Event) -> Self {
        CommsEvent::RelayClient(event)
    }
}

impl From<dcutr::Event> for CommsEvent {
    fn from(event: dcutr::Event) -> Self {
        CommsEvent::Dcutr(event)
    }
}

#[derive(Zeroize, ZeroizeOnDrop)]
struct MolecularChunk {
    payload: Vec<u8>,
}

pub struct P2PNetworkManager {
    swarm: Swarm<VolatileBehaviour>,
}

impl P2PNetworkManager {
    pub async fn new(local_key: identity::Keypair) -> Result<Self, Box<dyn Error>> {
        let local_peer_id = PeerId::from(local_key.public());
        
        let mut kad_config = libp2p::kad::KademliaConfig::default();
        let store = MemoryStore::new(local_peer_id);
        let kademlia = Kademlia::with_config(local_peer_id, store, kad_config);

        let identify = identify::Behaviour::new(identify::Config::new(
            "0xp2p/volatile/1.0.0".to_string(),
            local_key.public(),
        ));
        
        let (_relay_transport, relay_client) = relay_client::new(local_peer_id);
        let dcutr = dcutr::Behaviour::new(local_peer_id);

        let behaviour = VolatileBehaviour {
            kademlia,
            identify,
            relay_client,
            dcutr,
        };

        let swarm = libp2p::SwarmBuilder::with_existing_identity(local_key)
            .with_tokio()
            .with_tcp(
                tcp::Config::default(),
                noise::Config::new,
                yamux::Config::default,
            )?
            .with_quic() 
            .with_behaviour(|_| behaviour)?
            .build();

        Ok(P2PNetworkManager { swarm })
    }

    pub async fn connect_to_public_infrastructure(&mut self) -> Result<(), Box<dyn Error>> {
        let public_relays = [
            "/ip4/147.75.109.213/tcp/4001/p2p/QmaCpDMGvV2m2MXZPWJv9wURnH7F8Qw4Xzqr9ab1QHMLwg",
            "/ip4/147.75.70.221/tcp/4001/p2p/Qme8g49Cc1mEsKUeYvV2AZtjhfFiwKABRczb9ndCg1EZZG"
        ];

        for addr_str in public_relays {
            let addr: Multiaddr = addr_str.parse()?;
            if let Some(peer_id) = PeerId::try_from_multiaddr(&addr).ok() {
                self.swarm.behaviour_mut().kademlia.add_address(&peer_id, addr.clone());
                self.swarm.dial(addr)?;
            }
        }
        Ok(())
    }

    pub async fn run_molecular_pump(&mut self) -> Result<(), Box<dyn Error>> {
        loop {
            tokio::select! {
                event = self.swarm.select_next_some() => match event {
                    SwarmEvent::Behaviour(CommsEvent::Dcutr(dcutr::Event::RemoteInitiatedDirectConnectionUpgrade { remote_peer })) => {
                    }
                    _ => {}
                }
            }
        }
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    let local_key = identity::Keypair::generate_ed25519();
    let mut manager = P2PNetworkManager::new(local_key).await?;
    manager.connect_to_public_infrastructure().await?;
    manager.run_molecular_pump().await?;
    Ok(())
}