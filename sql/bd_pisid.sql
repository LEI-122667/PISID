CREATE DATABASE IF NOT EXISTS bd_pisid;
USE bd_pisid;

-- ─────────────────────────────────────────────
-- 1. Simulacao
-- ─────────────────────────────────────────────
CREATE TABLE Simulacao (
    IDSimulacao    INT            AUTO_INCREMENT PRIMARY KEY,
    Descricao      TEXT,
    Equipa         INT            UNIQUE, -- Added UNIQUE so Utilizador can reference it
    DataHoraInicio TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    Pontuacao      INT            DEFAULT 0,
    ArCondicionado BOOLEAN        DEFAULT FALSE,
    Ativo          BOOLEAN        DEFAULT TRUE  
);

-- ─────────────────────────────────────────────
-- 2. Utilizador
-- ─────────────────────────────────────────────
CREATE TABLE Utilizador (
    IDUtilizador   INT            AUTO_INCREMENT PRIMARY KEY,
    Nome           VARCHAR(100)   NOT NULL,
    Telemovel      VARCHAR(12),
    Tipo           ENUM('Admin','Criador','Leitor') NOT NULL,
    Email          VARCHAR(50)    UNIQUE,
    DataNascimento DATE,
    Equipa         INT,           -- References Simulacao(Equipa)
);

-- ─────────────────────────────────────────────
-- 3. MedicoesPassagens
-- ─────────────────────────────────────────────
CREATE TABLE MedicoesPassagens (
    IDSimulacao INT NOT NULL,
    IDMedicao   INT AUTO_INCREMENT PRIMARY KEY,
    Hora        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    SalaOrigem  INT,
    SalaDestino INT,
    Marsami     INT,
    Status      INT,
    MongoId     INT    NOT NULL,
    CONSTRAINT fk_medicoes_simulacao
        FOREIGN KEY (IDSimulacao) REFERENCES Simulacao(IDSimulacao)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- 4. Temperatura
-- ─────────────────────────────────────────────
CREATE TABLE Temperatura (
    IDSimulacao   INT            NOT NULL,
    IDTemperatura INT            AUTO_INCREMENT PRIMARY KEY,
    Hora          TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    Temperatura   DECIMAL(6,2),
    MongoId       INT    NOT NULL,
    CONSTRAINT fk_temperatura_simulacao
        FOREIGN KEY (IDSimulacao) REFERENCES Simulacao(IDSimulacao)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- 5. Som
-- ─────────────────────────────────────────────
CREATE TABLE Som (
    IDSimulacao INT            NOT NULL,
    IDSom       INT            AUTO_INCREMENT PRIMARY KEY,
    Hora        TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    Som         DECIMAL(6,2),
    MongoId     INT    NOT NULL,
    CONSTRAINT fk_som_simulacao
        FOREIGN KEY (IDSimulacao) REFERENCES Simulacao(IDSimulacao)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- 6. Mensagens
-- ─────────────────────────────────────────────
CREATE TABLE Mensagens (
    IDSimulacao INT          NOT NULL,
    ID          INT          AUTO_INCREMENT PRIMARY KEY,
    Hora        TIMESTAMP,
    Sala        INT,
    Sensor      VARCHAR(10),
    Leitura     DECIMAL(6,2),
    TipoAlerta  VARCHAR(50),
    Msg         VARCHAR(100),
    HoraEscrita TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_mensagens_simulacao
        FOREIGN KEY (IDSimulacao) REFERENCES Simulacao(IDSimulacao)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- 7. OcupacaoLabirinto
-- ─────────────────────────────────────────────
CREATE TABLE OcupacaoLabirinto (
    IDSimulacao         INT NOT NULL,
    IDJogo               INT NOT NULL,
    Sala                 INT NOT NULL,
    NumeroMarsamisOdd    INT DEFAULT 0,
    NumeroMarsamisEven   INT DEFAULT 0,
    Gatilho              INT DEFAULT 3,
    PRIMARY KEY (IDJogo, Sala),
    CONSTRAINT fk_ocupacao_simulacao
        FOREIGN KEY (IDSimulacao) REFERENCES Simulacao(IDSimulacao)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- 8. SetupMaze
-- ─────────────────────────────────────────────
CREATE TABLE SetupMaze (
    IDSimulacao                  INT            NOT NULL,
    IDSetup                      INT            AUTO_INCREMENT PRIMARY KEY,
    NumberRooms                  INT            NOT NULL,
    NumberMarsamis               INT            NOT NULL,
    NumberPlayers                INT,
    NormalTemperature            DECIMAL(6,2)   NOT NULL,
    TemperatureVarHighToleration DECIMAL(6,2)   NOT NULL,
    TemperatureVarLowToleration  DECIMAL(6,2)   NOT NULL,
    NormalNoise                  DECIMAL(6,2)   NOT NULL,
    NoiseVarToleration           DECIMAL(6,2)   NOT NULL,
    CONSTRAINT fk_setupmaze_simulacao
        FOREIGN KEY (IDSimulacao) REFERENCES Simulacao(IDSimulacao)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- 9. Corridor
-- ─────────────────────────────────────────────
CREATE TABLE Corridor (
    IDSimulacao INT     NOT NULL,
    IDCorridor  INT     AUTO_INCREMENT PRIMARY KEY,
    RoomA       INT     NOT NULL,
    RoomB       INT     NOT NULL,
    Fechado     BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_corridor_simulacao
        FOREIGN KEY (IDSimulacao) REFERENCES Simulacao(IDSimulacao)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- 10. ConfigJogo
-- ─────────────────────────────────────────────
CREATE TABLE ConfigJogo (
    IDSimulacao                  INT            NOT NULL,
    IDConfig                     INT            AUTO_INCREMENT PRIMARY KEY,
    outliers_temperatura         DECIMAL(6,2)   NOT NULL COMMENT 'Threshold to classify a temperature reading as an outlier',
    outliers_som                 DECIMAL(6,2)   NOT NULL COMMENT 'Threshold to classify a sound reading as an outlier',
    alerta_temperatura_high      INT            NOT NULL COMMENT 'Upper temperature value that triggers an alert',
    alerta_temperatura_low       INT            NOT NULL COMMENT 'Lower temperature value that triggers an alert',
    alerta_som                   INT            NOT NULL COMMENT 'Sound level that triggers an alert',
    time_fecharcorredores        INT            NOT NULL COMMENT 'Seconds until a closed corridor reopens',
    ruidolimite_fecharcorredores DECIMAL(5,2)   NOT NULL COMMENT 'Fraction (%) of the total sound limit that triggers corridor closure',
    CONSTRAINT fk_configjogo_simulacao
        FOREIGN KEY (IDSimulacao) REFERENCES Simulacao(IDSimulacao)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- TRIGGERS
-- ─────────────────────────────────────────────
DELIMITER $$

-- Enforce only one active simulation: When a new simulation is set to 'Ativo' = TRUE, 
-- set all others to FALSE. Note: MySQL triggers cannot update the same table easily 
-- without specific logic, so we use a 'BEFORE INSERT' to ensure consistency.

CREATE TRIGGER tr_OnlyOneActive_Insert
BEFORE INSERT ON Simulacao
FOR EACH ROW
BEGIN
    IF NEW.Ativo = TRUE THEN
        UPDATE Simulacao SET Ativo = FALSE WHERE Ativo = TRUE;
    END IF;
END$$

CREATE TRIGGER tr_OnlyOneActive_Update
BEFORE UPDATE ON Simulacao
FOR EACH ROW
BEGIN
    IF NEW.Ativo = TRUE AND OLD.Ativo = FALSE THEN
        UPDATE Simulacao SET Ativo = FALSE WHERE Ativo = TRUE;
    END IF;
END$$

DELIMITER ;
