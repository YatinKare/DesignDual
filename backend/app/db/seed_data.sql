-- Seed data for 6 system design problems
-- Each problem includes: prompt, constraints, rubric hints, phase time allocations

-- 1. URL Shortener (Apprentice)
INSERT INTO problems (
    id, slug, title, prompt, difficulty, focus_tags, constraints,
    estimated_time_minutes, phase_time_minutes, rubric_hints, sample_solution_outline
) VALUES (
    'url-shortener',
    'url-shortener',
    'Design a URL Shortener',
    'Design a URL shortening service like bit.ly that takes long URLs and returns short, unique aliases. Users should be able to create short URLs and be redirected when they visit them. Consider high read volume and global distribution.',
    'apprentice',
    '["scalability", "hashing", "caching", "database"]',
    '["Support 1 billion URLs", "Handle 10,000 read requests per second", "Short URLs must be unique and collision-free", "Redirects should be fast (<100ms)"]',
    30,
    '{"clarify": 5, "estimate": 5, "design": 12, "explain": 8}',
    '{"scoping": "Look for discussion of read-heavy workload, URL uniqueness constraints, and redirect speed requirements", "design": "Expect hash-based short URL generation, caching layer for hot URLs, SQL/NoSQL tradeoffs", "scale": "Should mention CDN for global distribution, cache hit ratios, database sharding strategies", "tradeoff": "Collision handling approaches, consistency vs availability for URL creation"}',
    'Hash-based ID generation (MD5/Base62), Redis cache for hot URLs, SQL database for URL mappings, CDN for global redirects, load balancer for API servers'
);

-- 2. Rate Limiter (Apprentice)
INSERT INTO problems (
    id, slug, title, prompt, difficulty, focus_tags, constraints,
    estimated_time_minutes, phase_time_minutes, rubric_hints, sample_solution_outline
) VALUES (
    'rate-limiter',
    'rate-limiter',
    'Design a Rate Limiter',
    'Design a distributed rate limiting system that can throttle requests to prevent abuse. The system should support different rate limits per user/API key and handle high throughput across multiple servers.',
    'apprentice',
    '["distributed_systems", "redis", "algorithms", "api_design"]',
    '["Support 100,000 requests per second", "Enforce limits per user or API key", "Limits: 1000 requests per hour, 10 requests per second", "Must work across multiple API servers"]',
    30,
    '{"clarify": 5, "estimate": 5, "design": 12, "explain": 8}',
    '{"scoping": "Identify rate limiting algorithms (token bucket, leaky bucket, sliding window), distributed coordination challenges", "design": "Expect Redis for shared state, discussion of atomic operations, time window handling", "scale": "Redis clustering, handling clock skew, performance under burst traffic", "tradeoff": "Consistency vs performance, fixed window vs sliding window algorithms, Redis vs in-memory caching"}',
    'Token bucket algorithm, Redis sorted sets for sliding window, atomic INCR operations, distributed coordination with Redis, fallback to local rate limiting if Redis fails'
);

-- 3. Spotify Backend (Sorcerer)
INSERT INTO problems (
    id, slug, title, prompt, difficulty, focus_tags, constraints,
    estimated_time_minutes, phase_time_minutes, rubric_hints, sample_solution_outline
) VALUES (
    'spotify',
    'spotify',
    'Design Spotify Backend',
    'Design the backend for a music streaming service like Spotify. Support user accounts, playlists, music catalog search, personalized recommendations, and audio streaming. Handle millions of concurrent users streaming music.',
    'sorcerer',
    '["streaming", "recommendations", "search", "cdn", "scalability"]',
    '["Support 100 million daily active users", "Handle 50,000 concurrent streams per region", "Catalog of 70 million songs", "Personalized recommendations update daily", "Audio streaming must be reliable (<1% buffering)"]',
    40,
    '{"clarify": 7, "estimate": 8, "design": 15, "explain": 10}',
    '{"scoping": "Distinguish read-heavy catalog operations from write-heavy user activity, identify streaming vs metadata services", "design": "Expect CDN for audio delivery, microservices for catalog/user/streaming, search index, recommendation pipeline", "scale": "CDN architecture, database partitioning (user data vs catalog), caching strategies for hot songs/playlists, ML model serving", "tradeoff": "SQL vs NoSQL for playlists, real-time vs batch recommendations, consistency models for playlist updates"}',
    'Microservices: User Service (PostgreSQL), Catalog Service (Elasticsearch), Streaming Service (CDN + origin servers), Recommendation Service (ML pipeline with batch jobs). Redis for session/playlist cache. Kafka for event streaming. CDN for audio file delivery.'
);

-- 4. WhatsApp / Chat System (Sorcerer)
INSERT INTO problems (
    id, slug, title, prompt, difficulty, focus_tags, constraints,
    estimated_time_minutes, phase_time_minutes, rubric_hints, sample_solution_outline
) VALUES (
    'chat-system',
    'chat-system',
    'Design WhatsApp / Chat System',
    'Design a real-time chat application like WhatsApp supporting one-on-one messaging, group chats, message history, online/offline status, and read receipts. Handle high message throughput and low latency delivery.',
    'sorcerer',
    '["real_time", "websockets", "message_queue", "consistency", "mobile"]',
    '["Support 1 billion users", "Deliver messages within 100ms", "Store message history for 1 year", "Support groups up to 256 members", "Handle 100,000 messages per second"]',
    40,
    '{"clarify": 7, "estimate": 8, "design": 15, "explain": 10}',
    '{"scoping": "Real-time delivery requirements, offline message storage, read receipt consistency, group chat fanout challenges", "design": "Expect WebSocket servers for persistent connections, message queue for async delivery, Cassandra/MongoDB for message history, presence service", "scale": "Connection server scaling, message queue partitioning, hot group handling, push notification integration", "tradeoff": "Eventual consistency for read receipts, message ordering guarantees, online status accuracy vs performance"}',
    'WebSocket servers for persistent connections, Kafka for message delivery queue, Cassandra for message storage (partitioned by user_id + timestamp), Redis for presence/online status, Push notification service for offline users. Load balancer with sticky sessions for WebSocket.'
);

-- 5. YouTube Backend (Archmage)
INSERT INTO problems (
    id, slug, title, prompt, difficulty, focus_tags, constraints,
    estimated_time_minutes, phase_time_minutes, rubric_hints, sample_solution_outline
) VALUES (
    'youtube',
    'youtube',
    'Design YouTube Backend',
    'Design the backend for a video streaming platform like YouTube. Support video uploads, transcoding, storage, streaming, comments, likes, recommendations, and view count tracking. Handle massive scale with billions of videos and millions of concurrent viewers.',
    'archmage',
    '["video_streaming", "storage", "cdn", "recommendations", "analytics", "transcoding"]',
    '["2 billion daily active users", "500 hours of video uploaded per minute", "Support 4K video streaming", "Recommendation engine updates hourly", "Track view counts in near real-time", "Store 10+ years of video content"]',
    50,
    '{"clarify": 8, "estimate": 10, "design": 20, "explain": 12}',
    '{"scoping": "Massive data volume (video storage), transcoding pipeline complexity, read-heavy streaming, write-heavy analytics", "design": "Expect object storage (S3/GCS) for videos, transcoding pipeline (queues + workers), CDN for delivery, separate services for metadata/comments/analytics, recommendation ML pipeline", "scale": "Multi-region CDN, blob storage replication, view count aggregation strategies, hot video caching, transcoding parallelization", "tradeoff": "Consistency models for view counts/likes, storage costs vs delivery speed, real-time vs batch analytics, video quality tiers"}',
    'Object storage (S3/GCS) for video blobs, Kafka for upload events, Transcoding workers (ffmpeg), CDN for video delivery, PostgreSQL for metadata, Cassandra for comments/likes, Redis for hot video metadata cache, Spark/Flink for analytics aggregation, ML recommendation service with feature store. Multi-region architecture with regional CDNs.'
);

-- 6. Google Docs Collaborative Editing (Archmage)
INSERT INTO problems (
    id, slug, title, prompt, difficulty, focus_tags, constraints,
    estimated_time_minutes, phase_time_minutes, rubric_hints, sample_solution_outline
) VALUES (
    'google-docs',
    'google-docs',
    'Design Google Docs Collaborative Editing',
    'Design a real-time collaborative document editing system like Google Docs. Multiple users should be able to simultaneously edit the same document with low-latency synchronization, conflict resolution, and full edit history. Support rich text formatting and offline editing.',
    'archmage',
    '["real_time", "crdt", "conflict_resolution", "operational_transform", "consistency", "offline"]',
    '["Support 50 simultaneous editors per document", "Synchronize edits within 50ms", "Handle offline editing with sync on reconnect", "Preserve complete edit history", "Support documents up to 50,000 words", "Never lose user edits"]',
    50,
    '{"clarify": 8, "estimate": 10, "design": 20, "explain": 12}',
    '{"scoping": "Conflict-free concurrent editing challenges, operational transform vs CRDT, offline editing requirements, version history storage", "design": "Expect operational transform or CRDT algorithm discussion, WebSocket for real-time sync, edit operation log, presence service, differential sync", "scale": "Hot document handling (many concurrent editors), operation broadcast efficiency, edit history compression, presence update frequency", "tradeoff": "Operational Transform vs CRDT complexity, server-side vs client-side merge, edit granularity (character vs word), eventual consistency guarantees"}',
    'Operational Transform (OT) or CRDT for conflict resolution, WebSocket servers for real-time sync, Redis pub/sub for operation broadcast, MongoDB/PostgreSQL for document storage and operation log, differential sync algorithm, vector clocks for causality, client-side cache for offline editing, snapshot mechanism for performance.'
);
