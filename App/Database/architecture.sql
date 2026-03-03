-- ============================================================
-- Caixinha de Perguntas - Database Architecture
-- Supports: SQLite and MariaDB/MySQL
-- ============================================================
-- 
-- TABLES:
--   usuarios    - User accounts and preferences
--   caixinhas   - Question boxes (shared cloud, any user can answer)
--   perguntas   - Questions/messages sent to each caixinha
--
-- NOTES:
--   - SQLite uses INTEGER PRIMARY KEY AUTOINCREMENT
--   - MariaDB uses INT AUTO_INCREMENT
--   - Both use DATETIME for timestamps (SQLite stores as TEXT)
--   - `deleted_at` enables soft-delete via DB.select()
--   - `id_nuvem` on caixinhas = NULL means public cloud
-- ============================================================

-- ── Usuarios ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS usuarios (
    id          BIGINT PRIMARY KEY,             -- Telegram user ID
    nome        TEXT NOT NULL,
    username    TEXT DEFAULT NULL,
    idioma      TEXT NOT NULL DEFAULT 'pt',      -- 'pt', 'en', 'es'
    fuso_horario TEXT NOT NULL DEFAULT 'America/Sao_Paulo',
    is_admin    INTEGER NOT NULL DEFAULT 0,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    deleted_at  DATETIME DEFAULT NULL
);

-- ── Caixinhas (Question Boxes) ──────────────────────────────
-- Caixinhas are shared in a "cloud" (nuvem) common to all users.
-- Any user can send a question to any active caixinha via deep link.
CREATE TABLE IF NOT EXISTS caixinhas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT, -- MariaDB: INT AUTO_INCREMENT
    uid             TEXT UNIQUE,                       -- UUID público para links externos
    titulo          TEXT NOT NULL,
    id_usuario      BIGINT NOT NULL,                   -- Owner (FK → usuarios.id)
    concluida       INTEGER NOT NULL DEFAULT 0,        -- 0=active, 1=completed
    publica         INTEGER NOT NULL DEFAULT 0,        -- 0=private (link only), 1=visible in search
    silenciada      INTEGER NOT NULL DEFAULT 0,        -- 0=notifications on, 1=muted
    total_perguntas INTEGER NOT NULL DEFAULT 0,        -- Counter cache
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    deleted_at      DATETIME DEFAULT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
);

CREATE INDEX IF NOT EXISTS idx_caixinhas_usuario ON caixinhas(id_usuario);
CREATE INDEX IF NOT EXISTS idx_caixinhas_publica ON caixinhas(publica, concluida);
-- Nota: idx_caixinhas_uid é criado pelo DAO via migração (_ensure_uid_column)

-- ── Perguntas (Questions / Messages) ────────────────────────
CREATE TABLE IF NOT EXISTS perguntas (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT, -- MariaDB: INT AUTO_INCREMENT
    id_caixinha         INTEGER NOT NULL,                  -- FK → caixinhas.id
    id_usuario_autor    BIGINT NOT NULL,                   -- FK → usuarios.id (who asked)
    pergunta            TEXT NOT NULL,
    resposta            TEXT DEFAULT NULL,
    anonima             INTEGER NOT NULL DEFAULT 0,        -- 1=anonymous
    respondida          INTEGER NOT NULL DEFAULT 0,        -- 1=answered by box owner
    autor_notificado    INTEGER NOT NULL DEFAULT 0,        -- 1=author notified about response
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    deleted_at          DATETIME DEFAULT NULL,
    FOREIGN KEY (id_caixinha) REFERENCES caixinhas(id),
    FOREIGN KEY (id_usuario_autor) REFERENCES usuarios(id)
);

CREATE INDEX IF NOT EXISTS idx_perguntas_caixinha ON perguntas(id_caixinha);
CREATE INDEX IF NOT EXISTS idx_perguntas_autor ON perguntas(id_usuario_autor);
CREATE INDEX IF NOT EXISTS idx_perguntas_respondida ON perguntas(id_caixinha, respondida);

-- ============================================================
-- MariaDB VARIANT (use instead of above for MariaDB/MySQL):
-- ============================================================
-- Replace:
--   INTEGER PRIMARY KEY AUTOINCREMENT  →  INT AUTO_INCREMENT PRIMARY KEY
--   BIGINT PRIMARY KEY                 →  BIGINT PRIMARY KEY
--   TEXT                                →  TEXT (or VARCHAR(N) for indexed cols)
--   DATETIME DEFAULT CURRENT_TIMESTAMP →  DATETIME DEFAULT CURRENT_TIMESTAMP
--   CREATE INDEX IF NOT EXISTS         →  CREATE INDEX IF NOT EXISTS (MariaDB 10.1.4+)
--
-- Example for MariaDB:
--
-- CREATE TABLE IF NOT EXISTS usuarios (
--     id          BIGINT PRIMARY KEY,
--     nome        VARCHAR(255) NOT NULL,
--     username    VARCHAR(255) DEFAULT NULL,
--     idioma      VARCHAR(5) NOT NULL DEFAULT 'pt',
--     is_admin    TINYINT NOT NULL DEFAULT 0,
--     created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
--     updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
--     deleted_at  DATETIME DEFAULT NULL
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
--
-- CREATE TABLE IF NOT EXISTS caixinhas (
--     id              INT AUTO_INCREMENT PRIMARY KEY,
--     titulo          VARCHAR(255) NOT NULL,
--     id_usuario      BIGINT NOT NULL,
--     concluida       TINYINT NOT NULL DEFAULT 0,
--     publica         TINYINT NOT NULL DEFAULT 1,
--     total_perguntas INT NOT NULL DEFAULT 0,
--     created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
--     updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
--     deleted_at      DATETIME DEFAULT NULL,
--     FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
--
-- CREATE TABLE IF NOT EXISTS perguntas (
--     id                  INT AUTO_INCREMENT PRIMARY KEY,
--     id_caixinha         INT NOT NULL,
--     id_usuario_autor    BIGINT NOT NULL,
--     pergunta            TEXT NOT NULL,
--     anonima             TINYINT NOT NULL DEFAULT 0,
--     respondida          TINYINT NOT NULL DEFAULT 0,
--     created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
--     updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
--     deleted_at          DATETIME DEFAULT NULL,
--     FOREIGN KEY (id_caixinha) REFERENCES caixinhas(id),
--     FOREIGN KEY (id_usuario_autor) REFERENCES usuarios(id)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
