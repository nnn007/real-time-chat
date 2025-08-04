// Real-Time Chat Application MongoDB Schema
// This script sets up collections, indexes, and validation rules for message storage

// Switch to the chat database
use('realtime_chat');

// Messages collection for storing encrypted chat messages
db.createCollection('messages', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['chatroom_id', 'user_id', 'content', 'message_type', 'created_at'],
      properties: {
        _id: {
          bsonType: 'objectId'
        },
        chatroom_id: {
          bsonType: 'string',
          description: 'UUID of the chatroom'
        },
        user_id: {
          bsonType: 'string',
          description: 'UUID of the message sender'
        },
        content: {
          bsonType: 'object',
          required: ['encrypted_data', 'iv'],
          properties: {
            encrypted_data: {
              bsonType: 'string',
              description: 'AES encrypted message content'
            },
            iv: {
              bsonType: 'string',
              description: 'Initialization vector for encryption'
            },
            key_version: {
              bsonType: 'int',
              description: 'Version of encryption key used'
            }
          }
        },
        message_type: {
          bsonType: 'string',
          enum: ['text', 'image', 'file', 'system'],
          description: 'Type of message content'
        },
        reply_to: {
          bsonType: ['objectId', 'null'],
          description: 'ID of message being replied to'
        },
        edited_at: {
          bsonType: ['date', 'null'],
          description: 'Timestamp when message was last edited'
        },
        deleted_at: {
          bsonType: ['date', 'null'],
          description: 'Timestamp when message was deleted (soft delete)'
        },
        reactions: {
          bsonType: 'array',
          items: {
            bsonType: 'object',
            required: ['user_id', 'emoji', 'created_at'],
            properties: {
              user_id: {
                bsonType: 'string',
                description: 'UUID of user who reacted'
              },
              emoji: {
                bsonType: 'string',
                description: 'Emoji reaction'
              },
              created_at: {
                bsonType: 'date',
                description: 'When reaction was added'
              }
            }
          }
        },
        attachments: {
          bsonType: 'array',
          items: {
            bsonType: 'object',
            required: ['filename', 'file_type', 'file_size', 'encrypted_url'],
            properties: {
              filename: {
                bsonType: 'string',
                description: 'Original filename'
              },
              file_type: {
                bsonType: 'string',
                description: 'MIME type of file'
              },
              file_size: {
                bsonType: 'int',
                description: 'File size in bytes'
              },
              encrypted_url: {
                bsonType: 'string',
                description: 'Encrypted URL to file storage'
              },
              thumbnail_url: {
                bsonType: ['string', 'null'],
                description: 'URL to thumbnail (for images/videos)'
              }
            }
          }
        },
        metadata: {
          bsonType: 'object',
          properties: {
            client_id: {
              bsonType: 'string',
              description: 'Client identifier for deduplication'
            },
            ip_address: {
              bsonType: 'string',
              description: 'Sender IP address (hashed for privacy)'
            },
            user_agent: {
              bsonType: 'string',
              description: 'Client user agent'
            },
            delivery_status: {
              bsonType: 'string',
              enum: ['sent', 'delivered', 'read'],
              description: 'Message delivery status'
            }
          }
        },
        created_at: {
          bsonType: 'date',
          description: 'Message creation timestamp'
        },
        updated_at: {
          bsonType: 'date',
          description: 'Last update timestamp'
        }
      }
    }
  }
});

// Chat summaries collection for AI-generated conversation summaries
db.createCollection('chat_summaries', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['chatroom_id', 'summary_text', 'message_count', 'start_date', 'end_date', 'created_at'],
      properties: {
        _id: {
          bsonType: 'objectId'
        },
        chatroom_id: {
          bsonType: 'string',
          description: 'UUID of the chatroom'
        },
        summary_text: {
          bsonType: 'string',
          description: 'AI-generated summary of conversation'
        },
        summary_type: {
          bsonType: 'string',
          enum: ['automatic', 'manual', 'scheduled'],
          description: 'How the summary was generated'
        },
        message_count: {
          bsonType: 'int',
          minimum: 1,
          description: 'Number of messages summarized'
        },
        start_date: {
          bsonType: 'date',
          description: 'Start of summarized time period'
        },
        end_date: {
          bsonType: 'date',
          description: 'End of summarized time period'
        },
        participants: {
          bsonType: 'array',
          items: {
            bsonType: 'string'
          },
          description: 'User IDs of conversation participants'
        },
        keywords: {
          bsonType: 'array',
          items: {
            bsonType: 'string'
          },
          description: 'Key topics extracted from conversation'
        },
        sentiment_score: {
          bsonType: 'double',
          minimum: -1,
          maximum: 1,
          description: 'Overall sentiment of conversation (-1 to 1)'
        },
        language: {
          bsonType: 'string',
          description: 'Primary language of conversation'
        },
        created_at: {
          bsonType: 'date',
          description: 'Summary creation timestamp'
        },
        created_by: {
          bsonType: ['string', 'null'],
          description: 'User ID who requested manual summary'
        }
      }
    }
  }
});

// Message search index collection for full-text search
db.createCollection('message_search_index', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['message_id', 'chatroom_id', 'user_id', 'searchable_content', 'created_at'],
      properties: {
        _id: {
          bsonType: 'objectId'
        },
        message_id: {
          bsonType: 'objectId',
          description: 'Reference to original message'
        },
        chatroom_id: {
          bsonType: 'string',
          description: 'UUID of the chatroom'
        },
        user_id: {
          bsonType: 'string',
          description: 'UUID of message sender'
        },
        searchable_content: {
          bsonType: 'string',
          description: 'Decrypted content for search indexing'
        },
        content_hash: {
          bsonType: 'string',
          description: 'Hash of content for integrity verification'
        },
        message_type: {
          bsonType: 'string',
          enum: ['text', 'image', 'file', 'system']
        },
        tags: {
          bsonType: 'array',
          items: {
            bsonType: 'string'
          },
          description: 'Extracted tags and keywords'
        },
        language: {
          bsonType: 'string',
          description: 'Detected language of content'
        },
        created_at: {
          bsonType: 'date',
          description: 'Original message timestamp'
        },
        indexed_at: {
          bsonType: 'date',
          description: 'When content was indexed'
        }
      }
    }
  }
});

// User activity collection for analytics and presence
db.createCollection('user_activity', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['user_id', 'chatroom_id', 'activity_type', 'timestamp'],
      properties: {
        _id: {
          bsonType: 'objectId'
        },
        user_id: {
          bsonType: 'string',
          description: 'UUID of the user'
        },
        chatroom_id: {
          bsonType: 'string',
          description: 'UUID of the chatroom'
        },
        activity_type: {
          bsonType: 'string',
          enum: ['join', 'leave', 'typing_start', 'typing_stop', 'message_read', 'online', 'offline'],
          description: 'Type of user activity'
        },
        timestamp: {
          bsonType: 'date',
          description: 'When activity occurred'
        },
        metadata: {
          bsonType: 'object',
          properties: {
            message_id: {
              bsonType: ['objectId', 'null'],
              description: 'Related message ID if applicable'
            },
            session_id: {
              bsonType: ['string', 'null'],
              description: 'User session identifier'
            },
            client_info: {
              bsonType: 'object',
              properties: {
                platform: {
                  bsonType: 'string'
                },
                browser: {
                  bsonType: 'string'
                },
                version: {
                  bsonType: 'string'
                }
              }
            }
          }
        }
      }
    }
  }
});

// Create indexes for optimal query performance

// Messages collection indexes
db.messages.createIndex({ 'chatroom_id': 1, 'created_at': -1 });
db.messages.createIndex({ 'user_id': 1, 'created_at': -1 });
db.messages.createIndex({ 'chatroom_id': 1, 'message_type': 1, 'created_at': -1 });
db.messages.createIndex({ 'reply_to': 1 });
db.messages.createIndex({ 'created_at': -1 });
db.messages.createIndex({ 'metadata.client_id': 1 }, { sparse: true });
db.messages.createIndex({ 'deleted_at': 1 }, { sparse: true });

// Compound index for efficient pagination
db.messages.createIndex({ 
  'chatroom_id': 1, 
  'deleted_at': 1, 
  'created_at': -1 
});

// Chat summaries indexes
db.chat_summaries.createIndex({ 'chatroom_id': 1, 'created_at': -1 });
db.chat_summaries.createIndex({ 'start_date': 1, 'end_date': 1 });
db.chat_summaries.createIndex({ 'keywords': 1 });
db.chat_summaries.createIndex({ 'participants': 1 });

// Message search index - Full text search
db.message_search_index.createIndex({ 
  'searchable_content': 'text',
  'tags': 'text'
}, {
  weights: {
    'searchable_content': 10,
    'tags': 5
  },
  name: 'content_text_index'
});

db.message_search_index.createIndex({ 'chatroom_id': 1, 'created_at': -1 });
db.message_search_index.createIndex({ 'message_id': 1 }, { unique: true });
db.message_search_index.createIndex({ 'user_id': 1, 'created_at': -1 });
db.message_search_index.createIndex({ 'language': 1 });

// User activity indexes
db.user_activity.createIndex({ 'user_id': 1, 'timestamp': -1 });
db.user_activity.createIndex({ 'chatroom_id': 1, 'timestamp': -1 });
db.user_activity.createIndex({ 'activity_type': 1, 'timestamp': -1 });
db.user_activity.createIndex({ 'timestamp': -1 });

// TTL index for automatic cleanup of old activity records (30 days)
db.user_activity.createIndex({ 'timestamp': 1 }, { expireAfterSeconds: 2592000 });

// Create aggregation pipelines for common queries

// Pipeline for getting recent messages with user info
const recentMessagesWithUsers = [
  {
    $match: {
      chatroom_id: "CHATROOM_ID_PLACEHOLDER",
      deleted_at: null
    }
  },
  {
    $sort: { created_at: -1 }
  },
  {
    $limit: 50
  },
  {
    $lookup: {
      from: "users",
      localField: "user_id",
      foreignField: "_id",
      as: "user_info",
      pipeline: [
        {
          $project: {
            username: 1,
            display_name: 1,
            avatar_url: 1
          }
        }
      ]
    }
  },
  {
    $unwind: "$user_info"
  },
  {
    $sort: { created_at: 1 }
  }
];

// Pipeline for search with relevance scoring
const searchMessages = [
  {
    $match: {
      $and: [
        { chatroom_id: "CHATROOM_ID_PLACEHOLDER" },
        { $text: { $search: "SEARCH_QUERY_PLACEHOLDER" } }
      ]
    }
  },
  {
    $addFields: {
      score: { $meta: "textScore" }
    }
  },
  {
    $sort: { score: { $meta: "textScore" }, created_at: -1 }
  },
  {
    $limit: 20
  },
  {
    $lookup: {
      from: "messages",
      localField: "message_id",
      foreignField: "_id",
      as: "message_data"
    }
  },
  {
    $unwind: "$message_data"
  }
];

// Store these pipelines as views for easy access
db.createView("recent_messages_view", "messages", recentMessagesWithUsers);

// Functions for common operations (stored as JavaScript functions)

// Function to clean up old messages based on retention policy
function cleanupOldMessages(chatroomId, retentionDays = 365) {
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - retentionDays);
  
  const result = db.messages.updateMany(
    {
      chatroom_id: chatroomId,
      created_at: { $lt: cutoffDate },
      deleted_at: null
    },
    {
      $set: { 
        deleted_at: new Date(),
        content: {
          encrypted_data: "DELETED",
          iv: "DELETED",
          key_version: 0
        }
      }
    }
  );
  
  return result.modifiedCount;
}

// Function to get chatroom statistics
function getChatroomStats(chatroomId) {
  const stats = db.messages.aggregate([
    {
      $match: {
        chatroom_id: chatroomId,
        deleted_at: null
      }
    },
    {
      $group: {
        _id: null,
        total_messages: { $sum: 1 },
        unique_users: { $addToSet: "$user_id" },
        first_message: { $min: "$created_at" },
        last_message: { $max: "$created_at" },
        message_types: {
          $push: "$message_type"
        }
      }
    },
    {
      $project: {
        total_messages: 1,
        unique_user_count: { $size: "$unique_users" },
        first_message: 1,
        last_message: 1,
        type_distribution: {
          $reduce: {
            input: "$message_types",
            initialValue: {},
            in: {
              $mergeObjects: [
                "$$value",
                {
                  $arrayToObject: [
                    [
                      {
                        k: "$$this",
                        v: {
                          $add: [
                            { $ifNull: [{ $getField: { field: "$$this", input: "$$value" } }, 0] },
                            1
                          ]
                        }
                      }
                    ]
                  ]
                }
              ]
            }
          }
        }
      }
    }
  ]).toArray();
  
  return stats[0] || null;
}

print("MongoDB schema and indexes created successfully!");
print("Collections created: messages, chat_summaries, message_search_index, user_activity");
print("All indexes and validation rules have been applied.");
print("Helper functions: cleanupOldMessages(), getChatroomStats()");

