-- ─────────────────────────────────────────────
-- DROP ALL TRIGGERS (safe re-run)
-- ─────────────────────────────────────────────
DROP TRIGGER IF EXISTS Alerta_Temperatura;
DROP TRIGGER IF EXISTS Alerta_Som;
DROP TRIGGER IF EXISTS Inserir_Marsamis;
DROP TRIGGER IF EXISTS Pontuacao_gatilho;
DROP TRIGGER IF EXISTS Alerta_Odd_Even;
DROP TRIGGER IF EXISTS Alerta_Odd_Even_Update;
DROP TRIGGER IF EXISTS Alerta_Odd_Even_Insert;
DROP TRIGGER IF EXISTS Finalizar_Simulacao_Temperatura;
DROP TRIGGER IF EXISTS Finalizar_Simulacao_Som;

-- ─────────────────────────────────────────────
-- 1. Alerta_Temperatura
-- ─────────────────────────────────────────────
DELIMITER $$

CREATE TRIGGER Alerta_Temperatura
AFTER INSERT ON Temperatura
FOR EACH ROW 
BEGIN
    DECLARE alertaSuperior INT;
    DECLARE alertaInferior INT;
    DECLARE limiteSuperior DECIMAL(6,2);
    DECLARE limiteInferior DECIMAL(6,2);
    DECLARE normalTemp DECIMAL(6,2);
    DECLARE tempHighTol DECIMAL(6,2);
    DECLARE tempLowTol DECIMAL(6,2);
    DECLARE arcondicionado TINYINT;

    -- Get alert thresholds
    SELECT COALESCE(alerta_temperatura_high, 0), COALESCE(alerta_temperatura_low, 0)
    INTO alertaSuperior, alertaInferior
    FROM ConfigJogo
    WHERE IDSimulacao = NEW.IDSimulacao
    LIMIT 1;
    
    -- Get baseline maze setup
    SELECT COALESCE(NormalTemperature, 0), COALESCE(TemperatureVarHighToleration, 0), COALESCE(TemperatureVarLowToleration, 0)
    INTO normalTemp, tempHighTol, tempLowTol
    FROM SetupMaze
    WHERE IDSimulacao = NEW.IDSimulacao
    LIMIT 1;
    
    -- Calculate limits
    SET limiteSuperior = normalTemp + tempHighTol;
    SET limiteInferior = normalTemp - tempLowTol;
    
    -- Check AC status
    SELECT COALESCE(ArCondicionado, 0)
    INTO arcondicionado
    FROM Simulacao
    WHERE IDSimulacao = NEW.IDSimulacao
    LIMIT 1;
    
    -- Logic: Trigger alert if temperature is an outlier and AC is OFF (0)
    IF (NEW.Temperatura >= (limiteSuperior - alertaSuperior) OR NEW.Temperatura <= (limiteInferior + alertaInferior)) AND arcondicionado = 0 THEN
    
        INSERT INTO Mensagens (IDSimulacao, Sensor, Leitura, TipoAlerta, Msg, HoraEscrita)
        VALUES (NEW.IDSimulacao, '1', NEW.Temperatura, 'Temperatura', 'Outlier na temperatura', NEW.Hora);
        
    END IF;

END$$

DELIMITER ;

-- ─────────────────────────────────────────────
-- 2. Alerta_Som
-- ─────────────────────────────────────────────
DELIMITER $$

CREATE TRIGGER Alerta_Som 
AFTER INSERT ON Som
FOR EACH ROW
BEGIN

    DECLARE alerta INT DEFAULT 0;
    DECLARE limite DECIMAL(6,2) DEFAULT 0;
    DECLARE normalNoise DECIMAL(6,2) DEFAULT 0;
    DECLARE noiseTol DECIMAL(6,2) DEFAULT 0;
    DECLARE corredoresAbertos INT DEFAULT 0;

    SELECT COALESCE(alerta_som, 0)
    INTO alerta
    FROM ConfigJogo
    WHERE IDSimulacao = NEW.IDSimulacao
    LIMIT 1;
    
    SELECT COALESCE(NormalNoise, 0), COALESCE(NoiseVarToleration, 0)
    INTO normalNoise, noiseTol
    FROM SetupMaze
    WHERE IDSimulacao = NEW.IDSimulacao
    LIMIT 1;
    
    SET limite = normalNoise + noiseTol;
    
    SELECT COUNT(*)
    INTO corredoresAbertos
    FROM Corridor
    WHERE IDSimulacao = NEW.IDSimulacao AND Fechado = 0;
    
    IF NEW.Som >= (limite - alerta) AND corredoresAbertos > 0 THEN
       
        INSERT INTO Mensagens (IDSimulacao, Sensor, Leitura, TipoAlerta, Msg, HoraEscrita)
        VALUES (NEW.IDSimulacao,'2', NEW.Som,'Som','Outlier no ruído',NEW.Hora);
        
    END IF;

END$$

DELIMITER ;

-- ─────────────────────────────────────────────
-- 3. Inserir_Marsamis
-- ─────────────────────────────────────────────
DELIMITER $$

CREATE TRIGGER Inserir_Marsamis 
AFTER INSERT ON MedicoesPassagens
FOR EACH ROW
BEGIN
    DECLARE v_ativo BOOLEAN;
    SELECT Ativo INTO v_ativo FROM Simulacao WHERE IDSimulacao = NEW.IDSimulacao;

    IF v_ativo = TRUE THEN
        IF MOD(NEW.Marsami, 2) = 0 THEN
            INSERT INTO OcupacaoLabirinto (IDSimulacao, IDJogo, Sala, NumeroMarsamisEven, NumeroMarsamisOdd)
            VALUES (NEW.IDSimulacao, NEW.IDSimulacao, NEW.SalaDestino, 1, 0)
            ON DUPLICATE KEY UPDATE NumeroMarsamisEven = NumeroMarsamisEven + 1;
            
            INSERT INTO OcupacaoLabirinto (IDSimulacao, IDJogo, Sala, NumeroMarsamisEven, NumeroMarsamisOdd)
            VALUES (NEW.IDSimulacao, NEW.IDSimulacao, NEW.SalaOrigem, -1, 0)
            ON DUPLICATE KEY UPDATE NumeroMarsamisEven = NumeroMarsamisEven - 1;
        ELSE
            INSERT INTO OcupacaoLabirinto (IDSimulacao, IDJogo, Sala, NumeroMarsamisEven, NumeroMarsamisOdd)
            VALUES (NEW.IDSimulacao, NEW.IDSimulacao, NEW.SalaDestino, 0, 1)
            ON DUPLICATE KEY UPDATE NumeroMarsamisOdd = NumeroMarsamisOdd + 1;
            
            INSERT INTO OcupacaoLabirinto (IDSimulacao, IDJogo, Sala, NumeroMarsamisEven, NumeroMarsamisOdd)
            VALUES (NEW.IDSimulacao, NEW.IDSimulacao, NEW.SalaOrigem, 0, -1)
            ON DUPLICATE KEY UPDATE NumeroMarsamisOdd = NumeroMarsamisOdd - 1;
        END IF;
    END IF;
END$$

DELIMITER ;

-- ─────────────────────────────────────────────
-- 4. Pontuacao_gatilho
-- ─────────────────────────────────────────────
DELIMITER $$

CREATE TRIGGER Pontuacao_gatilho 
BEFORE UPDATE ON OcupacaoLabirinto
FOR EACH ROW
BEGIN

    IF NEW.Gatilho < OLD.Gatilho THEN
    
    	IF NEW.NumeroMarsamisOdd = NEW.NumeroMarsamisEven AND NEW.NumeroMarsamisOdd > 0 THEN
        	UPDATE Simulacao
            SET Pontuacao = Pontuacao + 1
            WHERE IDSimulacao = NEW.IDSimulacao AND Ativo = TRUE;
        ELSE
            UPDATE Simulacao
            SET Pontuacao = Pontuacao - 0.5
            WHERE IDSimulacao = NEW.IDSimulacao AND Ativo = TRUE;
        END IF;
        
    END IF;

END$$

DELIMITER ;

-- ─────────────────────────────────────────────
-- 5. Alerta_Odd_Even (Insert + Update)
-- ─────────────────────────────────────────────
DELIMITER $$

CREATE TRIGGER Alerta_Odd_Even_Update
AFTER UPDATE ON OcupacaoLabirinto
FOR EACH ROW
BEGIN
    DECLARE v_ativo BOOLEAN;
    SELECT Ativo INTO v_ativo FROM Simulacao WHERE IDSimulacao = NEW.IDSimulacao;

    IF v_ativo = TRUE THEN
        IF NEW.NumeroMarsamisOdd = NEW.NumeroMarsamisEven AND NEW.NumeroMarsamisOdd > 0 AND NEW.Gatilho > 0 THEN
            INSERT INTO Mensagens (IDSimulacao, Sala, TipoAlerta, Msg, Sensor, Hora, Leitura)
            VALUES (NEW.IDSimulacao, NEW.Sala, 'Movimento', 'odd = even', '0', NOW(), NULL);
        END IF;
    END IF;
END$$

CREATE TRIGGER Alerta_Odd_Even_Insert
AFTER INSERT ON OcupacaoLabirinto
FOR EACH ROW
BEGIN
    DECLARE v_ativo BOOLEAN;
    SELECT Ativo INTO v_ativo FROM Simulacao WHERE IDSimulacao = NEW.IDSimulacao;

    IF v_ativo = TRUE THEN
        IF NEW.NumeroMarsamisOdd = NEW.NumeroMarsamisEven AND NEW.NumeroMarsamisOdd > 0 AND NEW.Gatilho > 0 THEN
            INSERT INTO Mensagens (IDSimulacao, Sala, TipoAlerta, Msg, Sensor, Hora, Leitura)
            VALUES (NEW.IDSimulacao, NEW.Sala, 'Movimento', 'odd = even', '0', NOW(), NULL);
        END IF;
    END IF;
END$$

DELIMITER ;

-- ─────────────────────────────────────────────
-- 6. Finalizar_Simulacao_Temperatura
-- ─────────────────────────────────────────────
DELIMITER $$

CREATE TRIGGER Finalizar_Simulacao_Temperatura
AFTER INSERT ON Temperatura
FOR EACH ROW
BEGIN
    DECLARE normalTemp DECIMAL(6,2);
    DECLARE tempHighTol DECIMAL(6,2);
    DECLARE tempLowTol DECIMAL(6,2);
    DECLARE limiteSuperior DECIMAL(6,2);
    DECLARE limiteInferior DECIMAL(6,2);

    SELECT NormalTemperature, TemperatureVarHighToleration, TemperatureVarLowToleration
    INTO normalTemp, tempHighTol, tempLowTol
    FROM SetupMaze
    WHERE IDSimulacao = NEW.IDSimulacao
    LIMIT 1;

    SET limiteSuperior = normalTemp + tempHighTol;
    SET limiteInferior = normalTemp - tempLowTol;

    IF NEW.Temperatura >= limiteSuperior OR NEW.Temperatura <= limiteInferior THEN
        UPDATE Simulacao SET Ativo = FALSE WHERE IDSimulacao = NEW.IDSimulacao;
        
        INSERT INTO Mensagens (IDSimulacao, Sensor, Leitura, TipoAlerta, Msg, HoraEscrita)
        VALUES (NEW.IDSimulacao, '1', NEW.Temperatura, 'Temperatura', 'Simulação terminada: Limite de temperatura atingido!', NEW.Hora);
    END IF;
END$$

-- ─────────────────────────────────────────────
-- 7. Finalizar_Simulacao_Som
-- ─────────────────────────────────────────────
CREATE TRIGGER Finalizar_Simulacao_Som
AFTER INSERT ON Som
FOR EACH ROW
BEGIN
    DECLARE normalNoise DECIMAL(6,2);
    DECLARE noiseTol DECIMAL(6,2);
    DECLARE limite DECIMAL(6,2);

    SELECT NormalNoise, NoiseVarToleration
    INTO normalNoise, noiseTol
    FROM SetupMaze
    WHERE IDSimulacao = NEW.IDSimulacao
    LIMIT 1;

    SET limite = normalNoise + noiseTol;

    IF NEW.Som >= limite THEN
        UPDATE Simulacao SET Ativo = FALSE WHERE IDSimulacao = NEW.IDSimulacao;
        
        INSERT INTO Mensagens (IDSimulacao, Sensor, Leitura, TipoAlerta, Msg, HoraEscrita)
        VALUES (NEW.IDSimulacao, '2', NEW.Som, 'Som', 'Simulação terminada: Limite de ruído atingido!', NEW.Hora);
    END IF;
END$$

DELIMITER ;
