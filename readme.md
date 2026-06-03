# 💬 Real-Time Chat API
A scalable real-time chat backend built with **FastAPI** and **WebSockets**, designed with a Discord/WhatsApp-style architecture — persistent channel membership with ephemeral presence tracking.
 
---
 
## ✨ Features
 
- **Real-time messaging** over WebSockets with JWT authentication
- **Group channels** — create groups, invite users, broadcast messages
- **Direct messages** — deterministic DM channel IDs prevent duplicate conversations
- **Persistent channel membership** via Redis — users stay in channels when they go offline
- **REST API** for channel management, message history, and contacts
- **Pydantic validation** on all WebSocket messages and REST request bodies
---
 
## 🛠 Tech Stack
 
| Layer | Technology | Why |
|---|---|---|
| Framework | FastAPI | Async-first, WebSocket support, automatic docs |
| Real-time | WebSockets | Bidirectional, low-latency message delivery |
| Auth | JWT (access + refresh tokens) | Stateless, scalable authentication |
| Channel membership | Redis Sets | O(1) membership checks, bidirectional user↔channel mapping |
| Message history | PostgreSQL (in progress) | Persistent, queryable message storage |
| Validation | Pydantic v2 | Schema enforcement on all inputs |
 
---
 
## 🏗 Architecture
 
The core insight driving this design is the separation between **membership** and **presence**:
 
- **Who is in a channel** → Redis (persistent, survives disconnects)
- **Who is online right now** → In-memory dict (ephemeral, per-server)
This mirrors how Discord and WhatsApp work — you remain a group member when you go offline, and messages queue for delivery when you reconnect.
 
```
Client
  │
  ├── WebSocket /ws?token=...     → real-time messaging
  └── REST /channels/...          → channel management
 
Server
  ├── ChannelsManager             → Redis-backed membership
  ├── WebSocketsManager           → in-memory presence/sockets
  └── MessagesManager             → message routing + storage
```
 
**Message routing flow:**
```
User sends message
  → validate JWT
  → validate message schema
  → fetch channel members from Redis
  → for each member:
      online  → deliver via WebSocket
      offline → queue missed message (Redis)
```
 
**DM channels** use a deterministic ID (`sorted([user1, user2]).join("-")`) so two users always share exactly one conversation regardless of who initiates.
 
---
 
## 🚀 Getting Started
 
### Prerequisites
- Python 3.12+
- Redis
- PostgreSQL
### Installation
 
```bash
git clone https://github.com/yourusername/chat-api
cd chat-api
pip install -r requirements.txt
```
 
### Environment Variables
 
```env
REDIS_HOST=localhost
REDIS_PORT=6379
DATABASE_URL=postgresql+asyncpg://user:password@localhost/chatdb
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
```
 
### Run
 
```bash
uvicorn src.main:app --reload
```
 
API docs available at `http://localhost:8000/docs`
 
---
 
## 📡 API Overview
 
### WebSocket
```
WS /ws?token=<access_token>
 
Send:  { "channel_id": "...", "content": "..." }
Recv:  { "sender": "...", "channel": "...", "content": "...", "message_type": "..." }
```
 
### REST Endpoints
 
| Method | Endpoint | Description |
|---|---|---|
| GET | `/channels/` | List user's channels |
| GET | `/channels/{channel_id}` | Get channel messages + members |
| POST | `/channels/create_group` | Create a group channel |
| POST | `/channels/invite` | Invite user to channel |
| POST | `/channels/add_contact` | Start a DM by email |
 
All REST endpoints require `Authorization: Bearer <token>`.
 
---
 
## 🗺 Roadmap
 
- [x] WebSocket real-time messaging
- [x] JWT authentication on WebSocket and REST
- [x] Redis-backed channel membership
- [x] Group channels and direct messages
- [x] Pydantic schema validation
- [x] PostgreSQL message persistence
- [ ] Missed message queue and delivery on reconnect
- [ ] Typing indicators
- [ ] Message read receipts
- [ ] Horizontal scaling via Redis Pub/Sub
- [ ] Rate limiting
---