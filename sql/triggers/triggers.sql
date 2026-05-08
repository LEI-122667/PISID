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
    DECLARE v_thresholdSuperior DECIMAL(6,2);
    DECLARE v_thresholdInferior DECIMAL(6,2);
    DECLARE v_arcondicionado TINYINT;

    SELECT
        (sm.NormalTemperature + sm.TemperatureVarHighToleration - cj.alerta_temperatura_high),
        (sm.NormalTemperature - sm.TemperatureVarLowToleration + cj.alerta_temperatura_low),
        s.ArCondicionado
    INTO v_thresholdSuperior, v_thresholdInferior, v_arcondicionado
    FROM Simulacao s
    JOIN SetupMaze sm ON sm.IDSimulacao = s.IDSimulacao
    JOIN ConfigJogo cj ON cj.IDSimulacao = s.IDSimulacao
    WHERE s.Ativo = TRUE
    ORDER BY s.IDSimulacao DESC
    LIMIT 1;

    IF v_thresholdSuperior IS NOT NULL THEN
        IF (NEW.Temperatura >= v_thresholdSuperior AND v_arcondicionado = 0)
        OR (NEW.Temperatura <= v_thresholdInferior AND v_arcondicionado = 1) THEN
            INSERT INTO Mensagens (IDSimulacao, Hora, Sala, Sensor, Leitura, TipoAlerta, Msg, HoraEscrita)
            SELECT s.IDSimulacao, NOW(), 0, '1', NEW.Temperatura, 'Temperatura', 'Temperatura perto do limite', NOW()
            FROM Simulacao s
            WHERE s.Ativo = TRUE
            ORDER BY s.IDSimulacao DESC
            LIMIT 1;
        END IF;
    END IF;
END$$

DELIMITER ;


-- ─────────────────────────────────────────────
-- 2. Alerta_Som
-- ─────────────────────────────────────────────
DELIMITER $$

DELIMITER $$

CREATE TRIGGER Alerta_Som
AFTER INSERT ON Som
FOR EACH ROW
BEGIN
    DECLARE v_limite DECIMAL(6,2);
    DECLARE v_alerta INT;
    DECLARE v_corredores INT;

    SELECT (sm.NormalNoise + sm.NoiseVarToleration - cj.alerta_som)
    INTO v_limite
    FROM Simulacao s
    JOIN SetupMaze sm ON sm.IDSimulacao = s.IDSimulacao
    JOIN ConfigJogo cj ON cj.IDSimulacao = s.IDSimulacao
    WHERE s.Ativo = TRUE
    ORDER BY s.IDSimulacao DESC
    LIMIT 1;

    SELECT COUNT(*) INTO v_corredores
    FROM Corridor c
    JOIN Simulacao s ON s.IDSimulacao = c.IDSimulacao
    WHERE s.Ativo = TRUE AND c.Fechado = 0;

    IF v_limite IS NOT NULL AND NEW.Som >= v_limite AND v_corredores > 0 THEN
        INSERT INTO Mensagens (IDSimulacao, Hora, Sala, Sensor, Leitura, TipoAlerta, Msg, HoraEscrita)
        SELECT s.IDSimulacao, NOW(), 0, '2', NEW.Som, 'Som', 'Som perto do limite', NOW()
        FROM Simulacao s
        WHERE s.Ativo = TRUE
        ORDER BY s.IDSimulacao DESC
        LIMIT 1;
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

    -- Only alert if simulation is active
    IF v_ativo = TRUE THEN
        -- Check if the current state satisfies the alert condition (Odd = Even > 0 and Gatilho > 0)
        IF NEW.NumeroMarsamisOdd = NEW.NumeroMarsamisEven 
           AND NEW.NumeroMarsamisOdd > 0 
           AND NEW.NumeroMarsamisEven > 0 
           AND NEW.Gatilho > 0 THEN
            
            -- Prevent spamming: only alert if the previous state did NOT satisfy the condition
            IF NOT (OLD.NumeroMarsamisOdd = OLD.NumeroMarsamisEven 
                    AND OLD.NumeroMarsamisOdd > 0 
                    AND OLD.NumeroMarsamisEven > 0 
                    AND OLD.Gatilho > 0) THEN
                
                INSERT INTO Mensagens (IDSimulacao, Sala, TipoAlerta, Msg, Sensor, Hora, Leitura)
                VALUES (NEW.IDSimulacao, NEW.Sala, 'Movimento', 'odd = even', '0', NOW(), NULL);
            END IF;
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
        -- For Insert, we just check the condition as there is no OLD state
        IF NEW.NumeroMarsamisOdd = NEW.NumeroMarsamisEven 
           AND NEW.NumeroMarsamisOdd > 0 
           AND NEW.NumeroMarsamisEven > 0 
           AND NEW.Gatilho > 0 THEN
            
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
