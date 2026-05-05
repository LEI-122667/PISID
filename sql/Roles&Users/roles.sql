-- ─────────────────────────────────────────────
-- ROLES
-- ─────────────────────────────────────────────

CREATE ROLE IF NOT EXISTS 'Admin';
CREATE ROLE IF NOT EXISTS 'Utilizador';
CREATE ROLE IF NOT EXISTS 'Android';
CREATE ROLE IF NOT EXISTS 'Agente';
CREATE ROLE IF NOT EXISTS 'ScriptSom';
CREATE ROLE IF NOT EXISTS 'ScriptTemperatura';
CREATE ROLE IF NOT EXISTS 'ScriptMovimento';

-- ─────────────────────────────────────────────
-- Admin
-- Read on Utilizador + SP execution (No direct CUD allowed)
-- ─────────────────────────────────────────────
GRANT SELECT ON bd_pisid.Utilizador TO 'Admin';

GRANT EXECUTE ON PROCEDURE bd_pisid.Criar_Utilizador    TO 'Admin';
GRANT EXECUTE ON PROCEDURE bd_pisid.Remover_Utilizador  TO 'Admin';
GRANT EXECUTE ON PROCEDURE bd_pisid.Alterar_Utilizador  TO 'Admin';

-- ─────────────────────────────────────────────
-- Utilizador
-- SP execution only
-- ─────────────────────────────────────────────
GRANT EXECUTE ON PROCEDURE bd_pisid.Alterar_Utilizador  TO 'Utilizador';
GRANT EXECUTE ON PROCEDURE bd_pisid.Criar_Jogo          TO 'Utilizador';
GRANT EXECUTE ON PROCEDURE bd_pisid.Alterar_Jogo        TO 'Utilizador';
GRANT EXECUTE ON PROCEDURE bd_pisid.Ler_Leaderboard     TO 'Utilizador';

-- ─────────────────────────────────────────────
-- Android
-- Read-only on relevant tables
-- ─────────────────────────────────────────────
GRANT SELECT ON bd_pisid.Utilizador         TO 'Android';
GRANT SELECT ON bd_pisid.Mensagens          TO 'Android';
GRANT SELECT ON bd_pisid.Temperatura        TO 'Android';
GRANT SELECT ON bd_pisid.OcupacaoLabirinto  TO 'Android';
GRANT SELECT ON bd_pisid.Som                TO 'Android';
GRANT SELECT ON bd_pisid.Simulacao          TO 'Android';
GRANT SELECT ON bd_pisid.ConfigJogo         TO 'Android';
GRANT SELECT ON bd_pisid.SetupMaze          TO 'Android';

-- ─────────────────────────────────────────────
-- AgentSimulacao
-- SP execution only
-- ─────────────────────────────────────────────
GRANT SELECT ON bd_pisid.ConfigJogo                 TO 'Agente';
GRANT SELECT ON bd_pisid.Corridor                   TO 'Agente';
GRANT SELECT ON bd_pisid.Som                        TO 'Agente';
GRANT SELECT ON bd_pisid.SetupMaze                  TO 'Agente';
GRANT EXECUTE ON PROCEDURE bd_pisid.Desligar_Ligar_ArCondicionado   TO 'Agente';
GRANT EXECUTE ON PROCEDURE bd_pisid.Ativar_Gatilho                  TO 'Agente';
GRANT EXECUTE ON PROCEDURE bd_pisid.Fechar_Abrir_Corredor           TO 'Agente';
GRANT EXECUTE ON PROCEDURE bd_pisid.Fechar_Abrir_TodosCorredores    TO 'Agente';
GRANT EXECUTE ON PROCEDURE bd_pisid.Ler_Alertas                     TO 'Agente';

-- ─────────────────────────────────────────────
-- Script roles
-- One SP each
-- ─────────────────────────────────────────────
GRANT EXECUTE ON PROCEDURE bd_pisid.Inserir_Som         TO 'ScriptSom';
GRANT EXECUTE ON PROCEDURE bd_pisid.Inserir_Temperatura TO 'ScriptTemperatura';
GRANT EXECUTE ON PROCEDURE bd_pisid.Inserir_Movimento   TO 'ScriptMovimento';
