use futures::StreamExt;
use libp2p::{
    dcutr, identity, identify,
    kad::{store::MemoryStore, Kademlia, KademliaConfig},
    noise, relay::client as relay_client,
    swarm::{NetworkBehaviour, SwarmEvent},
    tcp, quic, yamux, Multiaddr, PeerId, Swarm,
};
use std::error::Error;
use std::time::Duration;

#[derive(NetworkBehaviour)]
pub struct P2PBehaviour {
    pub kademlia: Kademlia<MemoryStore>,
    pub identify: identify::Behaviour,
    pub relay_client: relay_client::Behaviour,
    pub dcutr: dcutr::Behaviour,
}

pub struct P2PNetworkManager {
    swarm: Swarm<P2PBehaviour>,
}

impl P2PNetworkManager {
    pub async fn new(local_key: identity::Keypair) -> Result<Self, Box<dyn Error>> {
        let local_peer_id = PeerId::from(local_key.public());
        
        let store = MemoryStore::new(local_peer_id);
        let kademlia = Kademlia::with_config(local_peer_id, store, KademliaConfig::default());

        let identify = identify::Behaviour::new(identify::Config::new(
            "p2p/stream/1.0.0".to_string(),
            local_key.public(),
        ));
        
        let (_relay_transport, relay_client) = relay_client::new(local_peer_id);
        let dcutr = dcutr::Behaviour::new(local_peer_id);

        let behaviour = P2PBehaviour {
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
            .with_swarm_config(|c| c.with_idle_connection_timeout(Duration::from_secs(30)))
            .build();

        Ok(P2PNetworkManager { swarm })
    }

    pub async fn connect_infrastructure(&mut self) -> Result<(), Box<dyn Error>> {
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

    pub async fn start_event_loop(&mut self) -> Result<(), Box<dyn Error>> {
        loop {
            tokio::select! {
                event = self.swarm.select_next_some() => match event {
                    SwarmEvent::Behaviour(P2PBehaviourEvent::Dcutr(dcutr::Event::RemoteInitiatedDirectConnectionUpgrade { remote_peer })) => {
                        println!("[+] DCUTR Hole punching successful with peer: {}", remote_peer);
                    }
                    SwarmEvent::ConnectionEstablished { peer_id, .. } => {
                        println!("[+] Connection secured with peer: {}", peer_id);
                    }
                    _ => {}
                }
            }
        }
    }
}
