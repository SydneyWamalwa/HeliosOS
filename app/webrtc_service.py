# app/webrtc_service.py
import asyncio
import json
import logging
import os
import uuid
from typing import Dict, Optional, Any, List

import aiortc
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate, VideoStreamTrack
from aiortc.contrib.media import MediaPlayer, MediaRelay
from fastapi import WebSocket

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

class WebRTCService:
    """Service for handling WebRTC connections and streaming desktop content"""
    
    # Class variables to track connections and streams
    pc_connections: Dict[str, RTCPeerConnection] = {}
    active_streams: Dict[str, Any] = {}
    relay = MediaRelay()
    
    @classmethod
    async def create_peer_connection(cls, client_id: str) -> RTCPeerConnection:
        """Create a new peer connection for a client"""
        if client_id in cls.pc_connections:
            # Close existing connection if it exists
            await cls.close_peer_connection(client_id)
            
        # Create peer connection with STUN server for NAT traversal
        pc = RTCPeerConnection({
            "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
        })
        cls.pc_connections[client_id] = pc
        
        # Set up media source (X11 desktop capture)
        # This uses FFmpeg to capture the X11 display
        display = os.environ.get("DISPLAY", ":0")
        player = MediaPlayer(
            f"x11grab://{display}",
            format="x11grab",
            options={
                "video_size": "1280x720",
                "framerate": "30",
                "draw_mouse": "1",
            },
        )
        
        # Store the player for later cleanup
        cls.active_streams[client_id] = player
        
        # Use relay to allow multiple clients to receive the same stream
        if player.video:
            video = cls.relay.subscribe(player.video)
            pc.addTrack(video)
        
        # Handle connection state changes
        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info(f"Connection state for {client_id}: {pc.connectionState}")
            if pc.connectionState == "failed" or pc.connectionState == "closed":
                await cls.close_peer_connection(client_id)
        
        # Handle ICE connection state changes
        @pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            logger.info(f"ICE connection state for {client_id}: {pc.iceConnectionState}")
            if pc.iceConnectionState == "failed" or pc.iceConnectionState == "closed":
                await cls.close_peer_connection(client_id)
        
        # Handle data channel
        @pc.on("datachannel")
        def on_datachannel(channel):
            logger.info(f"Data channel established with {client_id}: {channel.label}")
            
            @channel.on("message")
            async def on_message(message):
                if isinstance(message, str):
                    try:
                        data = json.loads(message)
                        if data.get("type") == "command":
                            # Handle remote commands (could be used for keyboard/mouse control)
                            logger.info(f"Received command from {client_id}: {data.get('command')}")
                    except json.JSONDecodeError:
                        pass
        
        return pc
    
    @classmethod
    async def handle_offer(cls, client_id: str, offer: Dict[str, Any]) -> Dict[str, Any]:
        """Process an SDP offer from a client and create an answer"""
        # Create or get peer connection
        if client_id not in cls.pc_connections:
            pc = await cls.create_peer_connection(client_id)
        else:
            pc = cls.pc_connections[client_id]
        
        # Set remote description from offer
        offer_sdp = RTCSessionDescription(sdp=offer["sdp"], type=offer["type"])
        await pc.setRemoteDescription(offer_sdp)
        
        # Create answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        
        return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
    
    @classmethod
    async def handle_ice_candidate(cls, client_id: str, candidate: Dict[str, Any]) -> None:
        """Process an ICE candidate from a client"""
        if client_id in cls.pc_connections:
            pc = cls.pc_connections[client_id]
            candidate_obj = RTCIceCandidate(
                component=candidate.get("component", 0),
                foundation=candidate.get("foundation", ""),
                ip=candidate.get("ip", ""),
                port=candidate.get("port", 0),
                priority=candidate.get("priority", 0),
                protocol=candidate.get("protocol", ""),
                type=candidate.get("type", ""),
                sdpMid=candidate.get("sdpMid", ""),
                sdpMLineIndex=candidate.get("sdpMLineIndex", 0),
            )
            await pc.addIceCandidate(candidate_obj)
    
    @classmethod
    async def close_peer_connection(cls, client_id: str) -> None:
        """Close a peer connection for a client and clean up resources"""
        if client_id in cls.pc_connections:
            pc = cls.pc_connections[client_id]
            await pc.close()
            del cls.pc_connections[client_id]
            logger.info(f"Closed peer connection for client {client_id}")
        
        if client_id in cls.active_streams:
            player = cls.active_streams[client_id]
            player.stop()
            del cls.active_streams[client_id]
            logger.info(f"Stopped media stream for client {client_id}")
    
    @classmethod
    async def handle_websocket(cls, websocket: WebSocket) -> None:
        """Handle WebSocket connection for WebRTC signaling"""
        await websocket.accept()
        
        # Generate a unique client ID
        client_id = str(uuid.uuid4())
        logger.info(f"New WebRTC client connected: {client_id}")
        
        try:
            # Send client ID to the client
            await websocket.send_json({"type": "client_id", "client_id": client_id})
            
            # Handle messages
            async for message in websocket.iter_json():
                msg_type = message.get("type")
                
                if msg_type == "offer":
                    # Handle SDP offer
                    answer = await cls.handle_offer(client_id, message)
                    await websocket.send_json({"type": "answer", **answer})
                
                elif msg_type == "ice_candidate":
                    # Handle ICE candidate
                    await cls.handle_ice_candidate(client_id, message.get("candidate", {}))
                
                elif msg_type == "stats_request":
                    # Send connection stats
                    if client_id in cls.pc_connections:
                        pc = cls.pc_connections[client_id]
                        stats = await pc.getStats()
                        stats_dict = {str(k): v for k, v in stats.items()}
                        await websocket.send_json({"type": "stats", "stats": stats_dict})
                
                elif msg_type == "close":
                    # Handle explicit close request
                    await cls.close_peer_connection(client_id)
                    break
        
        except Exception as e:
            logger.error(f"WebRTC error for client {client_id}: {str(e)}")
        
        finally:
            # Clean up when the WebSocket is closed
            await cls.close_peer_connection(client_id)
            logger.info(f"WebRTC client disconnected: {client_id}")
    
    @classmethod
    def get_active_connections_count(cls) -> int:
        """Get the number of active WebRTC connections"""
        return len(cls.pc_connections)