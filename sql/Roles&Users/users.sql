-- ─────────────────────────────────────────────
-- USERS
-- ─────────────────────────────────────────────

CREATE USER 'admin_user'@'%'        IDENTIFIED BY 'admin';
CREATE USER 'utilizador_user'@'%'   IDENTIFIED BY 'utilizador';
CREATE USER 'android_user'@'%'      IDENTIFIED BY 'android';
CREATE USER 'agente_user'@'%'       IDENTIFIED BY 'agente';
CREATE USER 'script_som'@'%'        IDENTIFIED BY 'som';
CREATE USER 'script_temperatura'@'%' IDENTIFIED BY 'temp';
CREATE USER 'script_movimento'@'%'  IDENTIFIED BY 'mov';

-- ─────────────────────────────────────────────
-- ASSIGN ROLES
-- ─────────────────────────────────────────────

GRANT 'Admin'           TO 'admin_user'@'%';
GRANT 'Utilizador'      TO 'utilizador_user'@'%';
GRANT 'Android'         TO 'android_user'@'%';
GRANT 'Agente'          TO 'agente_user'@'%';
GRANT 'ScriptSom'       TO 'script_som'@'%';
GRANT 'ScriptTemperatura' TO 'script_temperatura'@'%';
GRANT 'ScriptMovimento' TO 'script_movimento'@'%';

-- ─────────────────────────────────────────────
-- SET DEFAULT ROLES (active on login)
-- ─────────────────────────────────────────────

SET DEFAULT ROLE 'Admin'            TO 'admin_user'@'%';
SET DEFAULT ROLE 'Utilizador'       TO 'utilizador_user'@'%';
SET DEFAULT ROLE 'Android'          TO 'android_user'@'%';
SET DEFAULT ROLE 'Agente'           TO 'agente_user'@'%';
SET DEFAULT ROLE 'ScriptSom'        TO 'script_som'@'%';
SET DEFAULT ROLE 'ScriptTemperatura' TO 'script_temperatura'@'%';
SET DEFAULT ROLE 'ScriptMovimento'  TO 'script_movimento'@'%';
