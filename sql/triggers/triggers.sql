-- ─────────────────────────────────────────────
-- DROP ALL TRIGGERS (safe re-run)
-- ─────────────────────────────────────────────
DROP TRIGGER IF EXISTS Alerta_Temperatura;
DROP TRIGGER IF EXISTS Alerta_Som;
DROP TRIGGER IF EXISTS Inserir_Marsamis;
DROP TRIGGER IF EXISTS Pontuacao_gatilho;
DROP TRIGGER IF EXISTS Alerta_Odd_Even_Update;
DROP TRIGGER IF EXISTS Alerta_Odd_Even_Insert;
DROP TRIGGER IF EXISTS Finalizar_Simulacao_Temperatura;
DROP TRIGGER IF EXISTS Finalizar_Simulacao_Som;
DROP TRIGGER IF EXISTS Finalizar_Simulacao_Marsami;

-- ─────────────────────────────────────────────
-- 1. Alerta_Temperatura
-- ─────────────────────────────────────────────
DELIMITER $$

CREATE TRIGGER Alerta_Temperatura
AFTER INSERT ON Temperatura
FOR EACH ROW 
BEGIN
    DECLARE v_IDSimulacao INT;
    DECLARE alertaSuperior INT;
    DECLARE alertaInferior INT;
    DECLARE limiteSuperior DECIMAL(6,2);
    DECLARE limiteInferior DECIMAL(6,2);
    DECLARE normalTemp DECIMAL(6,2);
    DECLARE tempHighTol DECIMAL(6,2);
    DECLARE tempLowTol DECIMAL(6,2);
    DECLARE arcondicionado TINYINT;

    -- Get the active simulation
    SELECT IDSimulacao INTO v_IDSimulacao
    FROM Simulacao
    WHERE Ativo = TRUE
    ORDER BY IDSimulacao DESC
    LIMIT 1;

    IF v_IDSimulacao IS NOT NULL THEN

        -- Get alert thresholds
        SELECT COALESCE(alerta_temperatura_high, 0), COALESCE(alerta_temperatura_low, 0)
        INTO alertaSuperior, alertaInferior
        FROM ConfigJogo
        WHERE IDSimulacao = v_IDSimulacao
        LIMIT 1;

        -- Get baseline maze setup
        SELECT COALESCE(NormalTemperature, 0), COALESCE(TemperatureVarHighToleration, 0), COALESCE(TemperatureVarLowToleration, 0)
        INTO normalTemp, tempHighTol, tempLowTol
        FROM SetupMaze
        WHERE IDSimulacao = v_IDSimulacao
        LIMIT 1;

        -- Calculate limits
        SET limiteSuperior = normalTemp + tempHighTol;
        SET limiteInferior = normalTemp - tempLowTol;

        -- Check AC status
        SELECT COALESCE(ArCondicionado, 0)
        INTO arcondicionado
        FROM Simulacao
        WHERE IDSimulacao = v_IDSimulacao
        LIMIT 1;

        -- Logic: High temp alert when AC is OFF, low temp alert when AC is ON
        IF (NEW.Temperatura >= (limiteSuperior - alertaSuperior) AND arcondicionado = 0)
           OR (NEW.Temperatura <= (limiteInferior + alertaInferior) AND arcondicionado = 1) THEN

            INSERT INTO Mensagens (IDSimulacao, Hora, Sala, Sensor, Leitura, TipoAlerta, Msg, HoraEscrita)
            VALUES (v_IDSimulacao, NOW(), 0, '1', NEW.Temperatura, 'Temperatura', 'Temperatura perto do limite', NOW());

        END IF;

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

    DECLARE v_IDSimulacao INT;
    DECLARE alerta INT DEFAULT 0;
    DECLARE limite DECIMAL(6,2) DEFAULT 0;
    DECLARE normalNoise DECIMAL(6,2) DEFAULT 0;
    DECLARE noiseTol DECIMAL(6,2) DEFAULT 0;
    DECLARE corredoresAbertos INT DEFAULT 0;

    -- Get the active simulation
    SELECT IDSimulacao INTO v_IDSimulacao
    FROM Simulacao
    WHERE Ativo = TRUE
    ORDER BY IDSimulacao DESC
    LIMIT 1;

    IF v_IDSimulacao IS NOT NULL THEN

        SELECT COALESCE(alerta_som, 0)
        INTO alerta
        FROM ConfigJogo
        WHERE IDSimulacao = v_IDSimulacao
        LIMIT 1;

        SELECT COALESCE(NormalNoise, 0), COALESCE(NoiseVarToleration, 0)
        INTO normalNoise, noiseTol
        FROM SetupMaze
        WHERE IDSimulacao = v_IDSimulacao
        LIMIT 1;

        SET limite = normalNoise + noiseTol;

        SELECT COUNT(*)
        INTO corredoresAbertos
        FROM Corridor
        WHERE IDSimulacao = v_IDSimulacao AND Fechado = 0;

        IF NEW.Som >= (limite - alerta) AND corredoresAbertos > 0 THEN

            INSERT INTO Mensagens (IDSimulacao, Hora, Sala, Sensor, Leitura, TipoAlerta, Msg, HoraEscrita)
            VALUES (v_IDSimulacao, NOW(), 0, '2', NEW.Som, 'Som', 'Som perto do limite', NOW());

        END IF;

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
            VALUES (NEW.IDSimulacao, NEW.IDSimulacao, NEW.SalaOrigem, 0, 0)
            ON DUPLICATE KEY UPDATE NumeroMarsamisEven = NumeroMarsamisEven - 1;
        ELSE
            INSERT INTO OcupacaoLabirinto (IDSimulacao, IDJogo, Sala, NumeroMarsamisEven, NumeroMarsamisOdd)
            VALUES (NEW.IDSimulacao, NEW.IDSimulacao, NEW.SalaDestino, 0, 1)
            ON DUPLICATE KEY UPDATE NumeroMarsamisOdd = NumeroMarsamisOdd + 1;
            
            INSERT INTO OcupacaoLabirinto (IDSimulacao, IDJogo, Sala, NumeroMarsamisEven, NumeroMarsamisOdd)
            VALUES (NEW.IDSimulacao, NEW.IDSimulacao, NEW.SalaOrigem, 0, 0)
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
-- 6. Finalizar_Simulacao_Marsami
-- ─────────────────────────────────────────────
DELIMITER $$

CREATE TRIGGER Finalizar_Simulacao_Marsami
AFTER INSERT ON MedicoesPassagens
FOR EACH ROW
BEGIN
    DECLARE v_TotalMarsamis INT;
    DECLARE v_MarsamisTerminados INT;

    -- Verificar se a mensagem é de finalização (RoomOrigin=0, RoomDestiny=0, Status=2)
    IF NEW.SalaOrigem = 0 AND NEW.SalaDestino = 0 AND NEW.Status = 2 THEN
        
        -- Obter o número total de marsamis configurados para esta simulação
        SELECT NumberMarsamis INTO v_TotalMarsamis 
        FROM SetupMaze 
        WHERE IDSimulacao = NEW.IDSimulacao 
        LIMIT 1;

        -- Contar quantos marsamis únicos já enviaram a mensagem de término
        SELECT COUNT(DISTINCT Marsami) INTO v_MarsamisTerminados
        FROM MedicoesPassagens
        WHERE IDSimulacao = NEW.IDSimulacao
          AND SalaOrigem = 0 
          AND SalaDestino = 0 
          AND Status = 2;

        -- Se todos os marsamis terminaram, desativa a simulação
        IF v_MarsamisTerminados >= v_TotalMarsamis THEN
            UPDATE Simulacao SET Ativo = FALSE WHERE IDSimulacao = NEW.IDSimulacao;
            
            INSERT INTO Mensagens (IDSimulacao, Hora, Sala, Sensor, Leitura, TipoAlerta, Msg, HoraEscrita)
            VALUES (NEW.IDSimulacao, NOW(), 0, '0', 0, 'Simulacao', 'Simulação terminada: Todos os marsamis concluíram o percurso!', NOW());
        END IF;
    END IF;
END$$

DELIMITER ;
