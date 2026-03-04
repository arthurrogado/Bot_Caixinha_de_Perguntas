-- ============================================================
-- Caixinha de Perguntas - Database Architecture (MariaDB/MySQL)
-- ============================================================

-- ── Usuarios ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS usuarios (
    id           BIGINT PRIMARY KEY,
    nome         VARCHAR(255) NOT NULL,
    username     VARCHAR(255) DEFAULT NULL,
    idioma       VARCHAR(5) NOT NULL DEFAULT 'pt',
    fuso_horario VARCHAR(64) NOT NULL DEFAULT 'America/Sao_Paulo',
    is_admin     TINYINT NOT NULL DEFAULT 0,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at   DATETIME DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── Caixinhas (Question Boxes) ──────────────────────────────
CREATE TABLE IF NOT EXISTS caixinhas (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    uid             VARCHAR(36) UNIQUE,
    titulo          VARCHAR(255) NOT NULL,
    id_usuario      BIGINT NOT NULL,
    concluida       TINYINT NOT NULL DEFAULT 0,
    publica         TINYINT NOT NULL DEFAULT 0,
    silenciada      TINYINT NOT NULL DEFAULT 0,
    total_perguntas INT NOT NULL DEFAULT 0,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at      DATETIME DEFAULT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX IF NOT EXISTS idx_caixinhas_usuario ON caixinhas(id_usuario);
CREATE INDEX IF NOT EXISTS idx_caixinhas_publica  ON caixinhas(publica, concluida);
CREATE INDEX IF NOT EXISTS idx_caixinhas_uid      ON caixinhas(uid);

-- ── Perguntas (Questions / Messages) ────────────────────────
CREATE TABLE IF NOT EXISTS perguntas (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    id_caixinha         INT NOT NULL,
    id_usuario_autor    BIGINT NOT NULL,
    pergunta            TEXT NOT NULL,
    resposta            TEXT DEFAULT NULL,
    anonima             TINYINT NOT NULL DEFAULT 0,
    respondida          TINYINT NOT NULL DEFAULT 0,
    autor_notificado    TINYINT NOT NULL DEFAULT 0,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at          DATETIME DEFAULT NULL,
    FOREIGN KEY (id_caixinha)      REFERENCES caixinhas(id),
    FOREIGN KEY (id_usuario_autor) REFERENCES usuarios(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX IF NOT EXISTS idx_perguntas_caixinha   ON perguntas(id_caixinha);
CREATE INDEX IF NOT EXISTS idx_perguntas_autor       ON perguntas(id_usuario_autor);
CREATE INDEX IF NOT EXISTS idx_perguntas_respondida  ON perguntas(id_caixinha, respondida);
