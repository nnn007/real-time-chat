// MongoDB Schema for Real-Time Chat Application
// This file is automatically executed when the MongoDB container starts

// Switch to the chat database
db = db.getSiblingDB('realtime_chat');

// Create collections with validation
db.createCollection("users", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["username", "email", "password_hash"],
            properties: {
                username: {
                    bsonType: "string",
                    minLength: 3,
                    maxLength: 50
                },
                email: {
                    bsonType: "string",
                    pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
                },
                password_hash: {
                    bsonType: "string"
                },
                first_name: {
                    bsonType: "string",
                    maxLength: 100
                },
                last_name: {
                    bsonType: "string",
                    maxLength: 100
                },
                avatar_url: {
                    bsonType: "string"
                },
                is_active: {
                    bsonType: "bool"
                },
                is_verified: {
                    bsonType: "bool"
                },
                created_at: {
                    bsonType: "date"
                },
                updated_at: {
                    bsonType: "date"
                }
            }
        }
    }
});

db.createCollection("chatrooms", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["name"],
            properties: {
                name: {
                    bsonType: "string",
                    minLength: 1,
                    maxLength: 100
                },
                description: {
                    bsonType: "string"
                },
                is_private: {
                    bsonType: "bool"
                },
                is_direct_message: {
                    bsonType: "bool"
                },
                created_by: {
                    bsonType: "objectId"
                },
                created_at: {
                    bsonType: "date"
                },
                updated_at: {
                    bsonType: "date"
                }
            }
        }
    }
});

db.createCollection("messages", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["chatroom_id", "user_id", "content"],
            properties: {
                chatroom_id: {
                    bsonType: "objectId"
                },
                user_id: {
                    bsonType: "objectId"
                },
                content: {
                    bsonType: "string",
                    minLength: 1
                },
                message_type: {
                    enum: ["text", "image", "file", "system"]
                },
                file_url: {
                    bsonType: "string"
                },
                file_name: {
                    bsonType: "string"
                },
                file_size: {
                    bsonType: "int"
                },
                is_edited: {
                    bsonType: "bool"
                },
                edited_at: {
                    bsonType: "date"
                },
                created_at: {
                    bsonType: "date"
                },
                updated_at: {
                    bsonType: "date"
                }
            }
        }
    }
});

db.createCollection("chatroom_members", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["chatroom_id", "user_id"],
            properties: {
                chatroom_id: {
                    bsonType: "objectId"
                },
                user_id: {
                    bsonType: "objectId"
                },
                role: {
                    enum: ["admin", "moderator", "member"]
                },
                joined_at: {
                    bsonType: "date"
                }
            }
        }
    }
});

db.createCollection("message_reactions", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["message_id", "user_id", "reaction_type"],
            properties: {
                message_id: {
                    bsonType: "objectId"
                },
                user_id: {
                    bsonType: "objectId"
                },
                reaction_type: {
                    bsonType: "string",
                    minLength: 1,
                    maxLength: 20
                },
                created_at: {
                    bsonType: "date"
                }
            }
        }
    }
});

db.createCollection("user_sessions", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["user_id", "session_token", "refresh_token", "expires_at"],
            properties: {
                user_id: {
                    bsonType: "objectId"
                },
                session_token: {
                    bsonType: "string"
                },
                refresh_token: {
                    bsonType: "string"
                },
                expires_at: {
                    bsonType: "date"
                },
                is_active: {
                    bsonType: "bool"
                },
                created_at: {
                    bsonType: "date"
                }
            }
        }
    }
});

db.createCollection("user_connections", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["user_id", "connection_id"],
            properties: {
                user_id: {
                    bsonType: "objectId"
                },
                connection_id: {
                    bsonType: "string"
                },
                is_active: {
                    bsonType: "bool"
                },
                last_seen: {
                    bsonType: "date"
                },
                created_at: {
                    bsonType: "date"
                }
            }
        }
    }
});

// Create indexes for better performance
db.users.createIndex({ "username": 1 }, { unique: true });
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "created_at": 1 });

db.chatrooms.createIndex({ "name": 1 });
db.chatrooms.createIndex({ "created_by": 1 });
db.chatrooms.createIndex({ "created_at": 1 });

db.messages.createIndex({ "chatroom_id": 1 });
db.messages.createIndex({ "user_id": 1 });
db.messages.createIndex({ "created_at": 1 });
db.messages.createIndex({ "chatroom_id": 1, "created_at": 1 });

db.chatroom_members.createIndex({ "chatroom_id": 1, "user_id": 1 }, { unique: true });
db.chatroom_members.createIndex({ "user_id": 1 });

db.message_reactions.createIndex({ "message_id": 1, "user_id": 1, "reaction_type": 1 }, { unique: true });
db.message_reactions.createIndex({ "message_id": 1 });

db.user_sessions.createIndex({ "session_token": 1 }, { unique: true });
db.user_sessions.createIndex({ "refresh_token": 1 }, { unique: true });
db.user_sessions.createIndex({ "user_id": 1 });
db.user_sessions.createIndex({ "expires_at": 1 });

db.user_connections.createIndex({ "connection_id": 1 }, { unique: true });
db.user_connections.createIndex({ "user_id": 1 });
db.user_connections.createIndex({ "is_active": 1 });

// Insert default admin user (password: admin123)
db.users.insertOne({
    username: "admin",
    email: "admin@chatapp.com",
    password_hash: "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KzqKqG", // admin123
    first_name: "Admin",
    last_name: "User",
    is_active: true,
    is_verified: true,
    created_at: new Date(),
    updated_at: new Date()
});

// Insert default chat room
db.chatrooms.insertOne({
    name: "General",
    description: "General discussion room",
    is_private: false,
    is_direct_message: false,
    created_by: db.users.findOne({ username: "admin" })._id,
    created_at: new Date(),
    updated_at: new Date()
});

// Add admin user to general room
db.chatroom_members.insertOne({
    chatroom_id: db.chatrooms.findOne({ name: "General" })._id,
    user_id: db.users.findOne({ username: "admin" })._id,
    role: "admin",
    joined_at: new Date()
});

print("MongoDB schema initialized successfully!"); 