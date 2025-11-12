"""
WebSocket server for Phase 4 RL Visualizer
Bridges Python RL environment with TypeScript client
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable
import websockets
from websockets.server import WebSocketServerProtocol

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RLWebSocketServer:
    """WebSocket server that sends game and model states to the visualizer client"""

    def __init__(self, host: str = "localhost", port: int = 8765, crop_region: Optional[Dict[str, int]] = None):
        self.host = host
        self.port = port
        self.clients: set[WebSocketServerProtocol] = set()
        self.server = None
        self.crop_region = crop_region

        # Control state
        self.is_paused = False
        self.speed = 1
        self.step_requested = False

        # Callbacks
        self.on_control_callback: Optional[Callable] = None
        self.on_spawn_callback: Optional[Callable] = None
        self.on_ready_callback: Optional[Callable] = None  # Called when client is ready

    async def start(self):
        """Start the WebSocket server"""
        logger.info(f"Starting WebSocket server on ws://{self.host}:{self.port}")
        self.server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port
        )
        logger.info("WebSocket server started")

    async def handle_client(self, websocket: WebSocketServerProtocol):
        """Handle a new client connection"""
        self.clients.add(websocket)
        client_addr = websocket.remote_address
        logger.info(f"Client connected: {client_addr}")

        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_addr}")
        finally:
            self.clients.discard(websocket)

    async def handle_message(self, websocket: WebSocketServerProtocol, message: str):
        """Handle incoming message from client"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')

            if msg_type == 'init':
                logger.info(f"Client initialized with clientID: {data.get('clientID')}")
                # Send crop region to client if available
                response = {'type': 'init_response'}
                if self.crop_region:
                    response['crop_region'] = self.crop_region
                    logger.info(f"Sending crop region to client: {self.crop_region}")
                await websocket.send(json.dumps(response))

            elif msg_type == 'spawn':
                tile = data.get('tile')
                logger.info(f"Client requesting spawn at tile: {tile}")
                # In RL mode, spawning is already handled by the game bridge during reset
                # Just acknowledge by sending current game state
                if hasattr(self, 'on_spawn_callback') and self.on_spawn_callback:
                    await self.on_spawn_callback(tile)

            elif msg_type == 'ready':
                logger.info("Client is ready to receive game state")
                # Client has fully initialized and is ready to receive game state
                if hasattr(self, 'on_ready_callback') and self.on_ready_callback:
                    await self.on_ready_callback()

            elif msg_type == 'heartbeat':
                # Client is requesting next game tick
                # Handled by the main game loop, just acknowledge
                pass

            elif msg_type == 'control':
                await self.handle_control(data)
            else:
                logger.warning(f"Unknown message type: {msg_type}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def handle_control(self, data: Dict[str, Any]):
        """Handle control commands from client"""
        command = data.get('command')

        if command == 'play':
            self.is_paused = False
            logger.info("Control: Play")

        elif command == 'pause':
            self.is_paused = True
            logger.info("Control: Pause")

        elif command == 'step':
            self.step_requested = True
            logger.info("Control: Step")

        elif command == 'reset':
            if self.on_control_callback:
                await self.on_control_callback('reset')
            logger.info("Control: Reset")

        elif command == 'speed':
            self.speed = data.get('speed', 1)
            logger.info(f"Control: Speed changed to {self.speed}x")

    async def broadcast_game_state(self, visual_state: Dict[str, Any]):
        """Broadcast game state to all connected clients"""
        message = {
            'type': 'game_state',
            'tick': visual_state['tick'],
            'visual_state': visual_state
        }
        await self.broadcast(message)

    async def broadcast_game_update(self, visual_state: Dict[str, Any], game_update: Dict[str, Any]):
        """Broadcast both visual state and game update to all connected clients"""
        message = {
            'type': 'game_update',
            'tick': visual_state['tick'],
            'visual_state': visual_state,
            'gameUpdate': game_update
        }
        await self.broadcast(message)

    async def broadcast_model_state(
        self,
        tick: int,
        observation: list,
        action_dict: Dict[str, Any],
        value: float,
        reward: float,
        cumulative_reward: float,
        attention_weights: Optional[list] = None
    ):
        """Broadcast model state to all connected clients"""
        message = {
            'type': 'model_state',
            'tick': tick,
            'observation': observation,
            'action': action_dict,
            'value_estimate': value,
            'reward': reward,
            'cumulative_reward': cumulative_reward
        }

        if attention_weights is not None:
            message['attention_weights'] = attention_weights

        await self.broadcast(message)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients"""
        if not self.clients:
            return

        message_str = json.dumps(message)
        disconnected = set()

        for client in self.clients:
            try:
                await client.send(message_str)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
            except Exception as e:
                logger.error(f"Error sending message to client: {e}")
                disconnected.add(client)

        # Remove disconnected clients
        self.clients -= disconnected

    def should_step(self) -> bool:
        """Check if the game should advance a step"""
        if self.step_requested:
            self.step_requested = False
            return True

        return not self.is_paused

    def get_step_delay(self) -> float:
        """Get the delay between steps based on speed"""
        if self.speed <= 0:
            return 0.1
        return 0.1 / self.speed  # Base delay of 100ms at 1x speed

    def on_control(self, callback: Callable):
        """Register a callback for control events"""
        self.on_control_callback = callback

    def on_spawn(self, callback: Callable):
        """Register a callback for spawn events"""
        self.on_spawn_callback = callback

    def on_ready(self, callback: Callable):
        """Register a callback for client ready events"""
        self.on_ready_callback = callback

    async def stop(self):
        """Stop the WebSocket server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("WebSocket server stopped")

    def has_clients(self) -> bool:
        """Check if any clients are connected"""
        return len(self.clients) > 0


async def main():
    """Test the WebSocket server"""
    server = RLWebSocketServer()
    await server.start()

    # Keep server running
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await server.stop()


if __name__ == '__main__':
    asyncio.run(main())
