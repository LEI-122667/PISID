-- Garante que as tabelas vão para o sítio certo
CREATE DATABASE IF NOT EXISTS bd_pisid;
USE bd_pisid;

CREATE TABLE Utilizador (
    IDUtilizador INT AUTO_INCREMENT PRIMARY KEY,
    Nome VARCHAR(100) NOT NULL,
    Telemovel VARCHAR(12),
    Tipo ENUM('Criador','Editor','Leitor','AdminBD','AdminSite') NOT NULL,
    Email VARCHAR(50) UNIQUE,
    DataNascimento DATE,
    Equipa INT
);

CREATE TABLE Simulacao (
    IDSimulacao INT AUTO_INCREMENT PRIMARY KEY,
    Descricao TEXT,
    Equipa INT,
    DataHoraInicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Pontuacao INT DEFAULT 0,
    ArCondicionado BOOLEAN DEFAULT FALSE,
    QuantasCorredoresFechados INT DEFAULT 0
);

CREATE TABLE MedicoesPassagens (
    IDMedicao INT AUTO_INCREMENT PRIMARY KEY,
    Hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    SalaOrigem INT,
    SalaDestino INT,
    Marsami INT,
    Status INT CHECK (Status IN (1,2))
);

CREATE TABLE Temperatura (
    IDTemperatura INT AUTO_INCREMENT PRIMARY KEY,
    Hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Temperatura VARCHAR(12)
);

CREATE TABLE Som (
    IDSom INT AUTO_INCREMENT PRIMARY KEY,
    Hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Som VARCHAR(12)
);

CREATE TABLE Mensagens (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    Hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Sala INT,
    Sensor VARCHAR(10),
    Leitura DECIMAL(6,2),
    TipoAlerta VARCHAR(50),
    Msg VARCHAR(100),
    HoraEscrita TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE OcupacaoLabirinto (
    IDJogo INT,
    Sala INT,
    NumeroMarsamisOdd INT DEFAULT 0,
    NumeroMarsamisEven INT DEFAULT 0,
    Gatilho INT DEFAULT 3,
    PRIMARY KEY (IDJogo, Sala)
);

CREATE TABLE SetupMaze (
    IDSetup INT AUTO_INCREMENT PRIMARY KEY,
    NumberRooms INT NOT NULL,
    NumberMarsamis INT NOT NULL,
    NumberPlayers INT,
    NormalTemperature DECIMAL(5,2) NOT NULL,
    TemperatureVarHighToleration DECIMAL(5,2) NOT NULL,
    TemperatureVarLowToleration DECIMAL(5,2) NOT NULL,
    NormalNoise DECIMAL(5,2) NOT NULL,
    NoiseVarToleration DECIMAL(5,2) NOT NULL
);

-- Trigger com sintaxe limpa para o Docker
DELIMITER //
CREATE TRIGGER decrementa_gatilho
BEFORE UPDATE ON OcupacaoLabirinto
FOR EACH ROW
BEGIN
    IF NEW.Gatilho >= 3 THEN
        SET NEW.Gatilho = NEW.Gatilho - 1;
    END IF;
END//
DELIMITER ;