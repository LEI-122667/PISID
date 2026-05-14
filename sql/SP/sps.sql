DELIMITER $$

CREATE PROCEDURE Alterar_Jogo(
    IN p_IDSimulacao    INT,
    IN p_Descricao      TEXT,
    IN p_Equipa         INT,
    IN p_DataHoraInicio TIMESTAMP,
    IN p_Pontuacao      INT,
    IN p_ArCondicionado BOOLEAN
)
BEGIN
    DECLARE v_Equipa    INT;
    DECLARE v_Ativo     BOOLEAN;
    DECLARE v_EquipaUtilizador INT;

    -- Check simulation exists
    IF NOT EXISTS (SELECT 1 FROM Simulacao WHERE IDSimulacao = p_IDSimulacao) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Simulação não encontrada';
    END IF;

    -- Get simulation data
    SELECT Equipa, Ativo INTO v_Equipa, v_Ativo
    FROM Simulacao
    WHERE IDSimulacao = p_IDSimulacao;

    -- Cannot alter an active simulation
    IF v_Ativo = TRUE THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Não é possível alterar uma simulação ativa';
    END IF;

    -- Get the calling user's team
    SELECT Equipa INTO v_EquipaUtilizador
    FROM Utilizador
    WHERE Email = REGEXP_REPLACE(USER(), '@[^@]+$', '');

    IF v_EquipaUtilizador IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Utilizador não encontrado';
    END IF;

    -- Check the simulation belongs to the calling user's team
    IF v_Equipa != v_EquipaUtilizador THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Não tem permissão para alterar esta simulação';
    END IF;

    UPDATE Simulacao
    SET
        Descricao      = COALESCE(p_Descricao,      Descricao),
        Equipa         = COALESCE(p_Equipa,          Equipa),
        DataHoraInicio = COALESCE(p_DataHoraInicio,  DataHoraInicio),
        Pontuacao      = COALESCE(p_Pontuacao,        Pontuacao),
        ArCondicionado = COALESCE(p_ArCondicionado,   ArCondicionado)
    WHERE IDSimulacao = p_IDSimulacao;

END$$

DELIMITER ;

DELIMITER $$

CREATE PROCEDURE Alterar_Utilizador(
    IN p_Nome           VARCHAR(100),
    IN p_Telemovel      VARCHAR(12),
    IN p_Email          VARCHAR(50),
    IN p_DataNascimento DATE
)
BEGIN
    DECLARE v_IDUtilizador INT;

    -- Get the ID of whoever is calling this SP based on their MySQL login email
    SELECT IDUtilizador INTO v_IDUtilizador
    FROM Utilizador
    WHERE Email = REGEXP_REPLACE(USER(), '@[^@]+$', '');

    -- Check the calling user was found in the table
    IF v_IDUtilizador IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Utilizador não encontrado';
    END IF;

    -- If trying to change email, check it isnt already taken by someone else
    IF p_Email IS NOT NULL AND EXISTS (
        SELECT 1 FROM Utilizador
        WHERE Email = p_Email AND IDUtilizador != v_IDUtilizador
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Email já está em uso';
    END IF;

    UPDATE Utilizador
    SET
        Nome           = COALESCE(p_Nome,           Nome),
        Telemovel      = COALESCE(p_Telemovel,      Telemovel),
        Email          = COALESCE(p_Email,          Email),
        DataNascimento = COALESCE(p_DataNascimento, DataNascimento)
    WHERE IDUtilizador = v_IDUtilizador;

END$$

DELIMITER ;

DELIMITER $$

CREATE PROCEDURE Admin_Alterar_Utilizador(
    IN p_IDUtilizador   INT,
    IN p_Nome           VARCHAR(100),
    IN p_Tipo           ENUM('Admin','User','Android'),
    IN p_Email          VARCHAR(50),
    IN p_Telemovel      VARCHAR(12),
    IN p_DataNascimento DATE,
    IN p_Equipa         INT
)
BEGIN
    DECLARE v_OldEmail VARCHAR(50);
    DECLARE v_OldTipo  VARCHAR(20);
    DECLARE v_NewRole  VARCHAR(50);
    DECLARE v_OldRole  VARCHAR(50);

    -- Get current data
    SELECT Email, Tipo INTO v_OldEmail, v_OldTipo 
    FROM Utilizador WHERE IDUtilizador = p_IDUtilizador;

    IF v_OldEmail IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Utilizador não encontrado';
    END IF;

    -- 1. Update Table
    UPDATE Utilizador
    SET
        Nome           = COALESCE(p_Nome,           Nome),
        Tipo           = COALESCE(p_Tipo,           Tipo),
        Email          = COALESCE(p_Email,          Email),
        Telemovel      = COALESCE(p_Telemovel,      Telemovel),
        DataNascimento = COALESCE(p_DataNascimento, DataNascimento),
        Equipa         = COALESCE(p_Equipa,         Equipa)
    WHERE IDUtilizador = p_IDUtilizador;

    -- 2. Handle MySQL User changes (if email changed)
    IF p_Email IS NOT NULL AND p_Email <> v_OldEmail THEN
        SET @sql_rename = CONCAT('RENAME USER ''', v_OldEmail, '''@''%'' TO ''', p_Email, '''@''%''');
        PREPARE stmt FROM @sql_rename; EXECUTE stmt; DEALLOCATE PREPARE stmt;
        SET v_OldEmail = p_Email;
    END IF;

    -- 3. Handle Role changes (if type changed)
    IF p_Tipo IS NOT NULL AND p_Tipo <> v_OldTipo THEN
        -- Map roles
        SET v_OldRole = CASE WHEN v_OldTipo = 'Admin' THEN 'Admin' WHEN v_OldTipo = 'User' THEN 'Utilizador' ELSE 'Android' END;
        SET v_NewRole = CASE WHEN p_Tipo    = 'Admin' THEN 'Admin' WHEN p_Tipo    = 'User' THEN 'Utilizador' ELSE 'Android' END;

        -- Revoke old, grant new
        SET @sql_rev = CONCAT('REVOKE `', v_OldRole, '` FROM ''', v_OldEmail, '''@''%''');
        PREPARE stmt FROM @sql_rev; EXECUTE stmt; DEALLOCATE PREPARE stmt;

        SET @sql_grant = CONCAT('GRANT `', v_NewRole, '` TO ''', v_OldEmail, '''@''%''');
        PREPARE stmt FROM @sql_grant; EXECUTE stmt; DEALLOCATE PREPARE stmt;

        SET @sql_def = CONCAT('SET DEFAULT ROLE `', v_NewRole, '` TO ''', v_OldEmail, '''@''%''');
        PREPARE stmt FROM @sql_def; EXECUTE stmt; DEALLOCATE PREPARE stmt;
    END IF;

END$$

DELIMITER ;

DELIMITER $$

CREATE PROCEDURE Ativar_Gatilho(
    IN p_SalaId INT,
    IN p_Gatilho INT
)
BEGIN

	-- 1. DECLARAÇÃO DE VARIÁVEIS
    DECLARE v_IDSimulacao INT;
    DECLARE v_NGatilhoSala INT;
    DECLARE v_DiferencaGatilho INT;

    -- 2. HANDLER PARA ERROS TÉCNICOS (Retorna 0)
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SELECT 0 AS Result;
    END;

    -- 3. VERIFICAR SE EXISTE UMA SIMULAÇÃO ATIVA
    SELECT IDSimulacao INTO v_IDSimulacao
    FROM Simulacao
    WHERE Ativo = TRUE
    LIMIT 1;

    IF v_IDSimulacao IS NULL THEN
        -- Retorna -1: Não há jogo a decorrer
        SELECT -1 AS Result;

    ELSE

    	-- 4. VERIFICA SE GATILHO DA SALA FICA IGUAL OU MENOR QUE 0
    	SELECT Gatilho INTO v_NGatilhoSala
    	FROM OcupacaoLabirinto
    	WHERE Sala = p_SalaId AND IDSimulacao = v_IDSimulacao
    	LIMIT 1;

        IF v_NGatilhoSala IS NULL THEN
        	-- Retorna -1: Sala não existe
        	SELECT -1 AS Result;

        ELSE
        	SET v_DiferencaGatilho = v_NGatilhoSala - p_Gatilho;

        	IF v_DiferencaGatilho < 0 THEN
    			-- Retorna -1: Não há gatilhos suficientes para decrementar
    			SELECT -1 AS Result;

        	ELSE
        		UPDATE OcupacaoLabirinto
        		SET Gatilho = v_DiferencaGatilho
      			WHERE Sala = p_SalaId AND IDSimulacao = v_IDSimulacao;

        		-- Se chegámos aqui sem disparar o Handler, a operação foi concluída
        		-- Retornamos 1 indicando que o estado atual da DB é o solicitado
        		SELECT 1 AS Result;
            END IF;
    	END IF;
    END IF;

END$$

DELIMITER ;

DELIMITER $$

CREATE PROCEDURE Criar_Jogo(
    IN p_Descricao      TEXT,
    IN p_Equipa         INT,
    IN p_DataHoraInicio TIMESTAMP,
    IN p_Pontuacao      INT,
    IN p_ArCondicionado BOOLEAN,
    IN p_IDUtilizador   INT,
    OUT p_IDSimulacao   INT
)
BEGIN
    -- Check no active simulation already exists
    IF EXISTS (SELECT 1 FROM Simulacao WHERE Ativo = TRUE) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Já existe um jogo ativo, não é possível criar outro';
    END IF;

    -- Check team doesn't already have an active simulation
    IF EXISTS (SELECT 1 FROM Simulacao WHERE Equipa = p_Equipa AND Ativo = TRUE) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'A sua equipa já tem uma simulação ativa';
    END IF;

    INSERT INTO Simulacao (Descricao, Equipa, DataHoraInicio, Pontuacao, ArCondicionado, Ativo, IDUtilizador)
    VALUES (
        p_Descricao,
        p_Equipa,
        COALESCE(p_DataHoraInicio, CURRENT_TIMESTAMP),
        COALESCE(p_Pontuacao, 0),
        COALESCE(p_ArCondicionado, FALSE),
        TRUE,
        p_IDUtilizador
    );

    SET p_IDSimulacao = LAST_INSERT_ID();
END$$

DELIMITER ;

DELIMITER $$

CREATE PROCEDURE Criar_Utilizador(
    IN p_Nome           VARCHAR(100),
    IN p_Tipo           ENUM('Admin','User','Android'),
    IN p_Email          VARCHAR(150),
    IN p_Telemovel      VARCHAR(20),
    IN p_DataNascimento DATE,
    IN p_Equipa         INT,
    IN p_Password       VARCHAR(100)
)
BEGIN
    DECLARE v_Role VARCHAR(50);

    IF p_Nome IS NULL OR TRIM(p_Nome) = '' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Nome é obrigatório';
    END IF;
    IF p_Tipo IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Tipo é obrigatório';
    END IF;
    IF p_Email IS NULL OR TRIM(p_Email) = '' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Email é obrigatório';
    END IF;
    IF EXISTS (SELECT 1 FROM Utilizador WHERE Email = p_Email) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Email já está em uso';
    END IF;

    INSERT INTO Utilizador (Nome, Telemovel, Tipo, Email, DataNascimento, Equipa)
    VALUES (p_Nome, p_Telemovel, p_Tipo, p_Email, p_DataNascimento, p_Equipa);

    IF p_Tipo = 'Admin' THEN
        SET v_Role = 'Admin';
    ELSEIF p_Tipo = 'User' THEN
        SET v_Role = 'Utilizador';
    ELSEIF p_Tipo = 'Android' THEN
        SET v_Role = 'Android';
    END IF;

    SET @sql_create = CONCAT(
        'CREATE USER IF NOT EXISTS ''', p_Email, '''@''%'' IDENTIFIED BY ''', p_Password, ''''
    );
    PREPARE stmt FROM @sql_create;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;

    SET @sql_alter = CONCAT(
        'ALTER USER ''', p_Email, '''@''%'' IDENTIFIED BY ''', p_Password, ''''
    );
    PREPARE stmt FROM @sql_alter;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;

    SET @sql_grant = CONCAT(
        'GRANT `', v_Role, '` TO ''', p_Email, '''@''%'''
    );
    PREPARE stmt FROM @sql_grant;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;

    SET @sql_default = CONCAT(
        'SET DEFAULT ROLE `', v_Role, '` TO ''', p_Email, '''@''%'''
    );
    PREPARE stmt FROM @sql_default;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;

END$$

DELIMITER ;

DELIMITER $$

CREATE PROCEDURE Desligar_Ligar_ArCondicionado(
    IN p_Estado BOOLEAN
)
BEGIN
    -- 1. DECLARAÇÃO DE VARIÁVEIS (Sempre primeiro!)
    DECLARE v_IDSimulacao INT;

    -- 2. HANDLER PARA ERROS TÉCNICOS (Retorna 0 se o MySQL falhar)
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SELECT 0 AS Result;
    END;

    -- 3. VERIFICAR SE EXISTE UMA SIMULAÇÃO ATIVA
    SELECT IDSimulacao INTO v_IDSimulacao
    FROM Simulacao
    WHERE Ativo = TRUE
    LIMIT 1;

    -- 4. LÓGICA DE EXECUÇÃO E FEEDBACK
    IF v_IDSimulacao IS NULL THEN
        -- Retorna -1: Não há jogo a decorrer para alterar o AC
        SELECT -1 AS Result;

    ELSE
        -- Tentar atualizar o estado
        UPDATE Simulacao
        SET ArCondicionado = p_Estado
        WHERE IDSimulacao = v_IDSimulacao;

        -- Se chegámos aqui sem disparar o Handler, a operação foi concluída
        -- Retornamos 1 indicando que o estado atual da DB é o solicitado
        SELECT 1 AS Result;

    END IF;
END$$

DELIMITER ;

DELIMITER $$

CREATE PROCEDURE Fechar_Abrir_Corredor(
    IN p_CorredorId INT,
    IN p_Estado BOOlEAN
)
BEGIN

	-- 1. DECLARAÇÃO DE VARIÁVEIS
    DECLARE v_IDSimulacao INT;
    DECLARE v_CorredorExiste BOOLEAN;

    -- 2. HANDLER PARA ERROS TÉCNICOS (Retorna 0)
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SELECT 0 AS Result;
    END;

    -- 3. VERIFICAR SE EXISTE UMA SIMULAÇÃO ATIVA
    SELECT IDSimulacao INTO v_IDSimulacao
    FROM Simulacao
    WHERE Ativo = TRUE
    LIMIT 1;

    IF v_IDSimulacao IS NULL THEN
        -- Retorna -1: Não há jogo a decorrer
        SELECT -1 AS Result;

    ELSE
    	SELECT EXISTS (
            SELECT 1
            FROM Corridor
            WHERE IDCorridor = p_CorredorId AND IDSimulacao = v_IDSimulacao
        ) INTO v_CorredorExiste;

        IF v_CorredorExiste = 0 THEN
        	-- Retorna -1: Corredor não existe
    		SELECT -1 AS Result;

        ELSE
        	UPDATE Corridor
        	SET Fechado = p_Estado
        	WHERE IDCorridor = p_CorredorId AND IDSimulacao = v_IDSimulacao;

        	-- Se chegámos aqui sem disparar o Handler, a operação foi concluída
        	-- Retornamos 1 indicando que o estado atual da DB é o solicitado
        	SELECT 1 AS Result;
    	END IF;
    END IF;

END$$

DELIMITER ;

DELIMITER $$

CREATE PROCEDURE Fechar_Abrir_TodosCorredores(
    IN p_Estado BOOlEAN
)
BEGIN

	-- 1. DECLARAÇÃO DE VARIÁVEIS
    DECLARE v_IDSimulacao INT;

    -- 2. HANDLER PARA ERROS TÉCNICOS (Retorna 0)
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SELECT 0 AS Result;
    END;

    -- 3. VERIFICAR SE EXISTE UMA SIMULAÇÃO ATIVA
    SELECT IDSimulacao INTO v_IDSimulacao
    FROM Simulacao
    WHERE Ativo = TRUE
    LIMIT 1;

    IF v_IDSimulacao IS NULL THEN
        -- Retorna -1: Não há jogo a decorrer
        SELECT -1 AS Result;

    ELSE
    	UPDATE Corridor
        SET Fechado = p_Estado
        WHERE IDSimulacao = v_IDSimulacao AND Fechado != p_Estado;

        -- Se chegámos aqui sem disparar o Handler, a operação foi concluída
        -- Retornamos 1 indicando que o estado atual da DB é o solicitado
        SELECT 1 AS Result;
    END IF;

END$$

DELIMITER ;

DELIMITER $$

CREATE PROCEDURE Inserir_Movimento(
    IN p_MongoId INT,
    IN p_Hora TIMESTAMP,
    IN p_SalaOrigem INT,
    IN p_SalaDestino INT,
    IN p_Marsami INT,
    IN p_Status INT
)
BEGIN
    -- 1. DECLARAÇÃO DE VARIÁVEIS
    DECLARE v_IDSimulacao INT;
    DECLARE v_MaxRooms INT;
    DECLARE v_CountMongo INT;
    DECLARE v_CorredorExiste INT DEFAULT 0;
    DECLARE v_CountDupMovimento INT DEFAULT 0;
    DECLARE v_LastRoom INT DEFAULT NULL;

    -- 2. HANDLER PARA ERROS TÉCNICOS (Retorna 0)
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SELECT 0 AS Result;
    END;

    -- 3. VALIDAÇÕES INICIAIS (Nulos e Duplicados)
    IF p_MongoId IS NULL OR p_Marsami IS NULL OR p_Status IS NULL
       OR p_SalaOrigem IS NULL OR p_SalaDestino IS NULL THEN
        SELECT -1 AS Result;
    ELSE
        -- Verificar duplicado na tabela MedicoesPassagens (mesmo MongoId)
        SELECT COUNT(*) INTO v_CountMongo FROM MedicoesPassagens WHERE MongoId = p_MongoId;
        IF v_CountMongo > 0 THEN
            SELECT -2 AS Result;
        ELSE
            -- 4. OBTER CONTEXTO DA SIMULAÇÃO
            SELECT IDSimulacao INTO v_IDSimulacao FROM Simulacao WHERE Ativo = TRUE LIMIT 1;

            -- Se não houver simulação ativa ou data futura
            IF v_IDSimulacao IS NULL OR p_Hora > NOW() + INTERVAL 30 SECOND THEN
                SELECT -1 AS Result;
            ELSE
                -- Obter o número máximo de salas configurado para esta simulação
                SELECT NumberRooms INTO v_MaxRooms FROM SetupMaze WHERE IDSimulacao = v_IDSimulacao LIMIT 1;

                -- Obter a última sala onde o Marsami esteve (usando SalaDestino)
                SELECT SalaDestino INTO v_LastRoom
                FROM MedicoesPassagens
                WHERE IDSimulacao = v_IDSimulacao AND Marsami = p_Marsami
                ORDER BY MongoId DESC
                LIMIT 1;

                -- 5. VALIDAÇÃO DE REGRAS (Dado Inválido -1)
                IF p_Marsami <= 0 OR p_Status NOT IN (0, 1, 2)
                   OR p_SalaOrigem < 0 OR p_SalaDestino < 0
                   OR p_SalaOrigem > v_MaxRooms OR p_SalaDestino > v_MaxRooms THEN
                    SELECT -1 AS Result;

                -- Validar continuidade de movimento: se não é a primeira entrada (SalaOrigem != 0),
                -- a SalaOrigem deve ser a v_LastRoom
                ELSEIF p_SalaOrigem != 0 AND (v_LastRoom IS NULL OR v_LastRoom != p_SalaOrigem) THEN
                    SELECT -1 AS Result;

                -- Regra Status 0: Origem deve ser 0 (entrada no labirinto)
                ELSEIF p_Status = 0 AND p_SalaOrigem != 0 THEN
                    SELECT -1 AS Result;

                -- Regra SalaOrigem=0 e SalaDestino=0: Status deve ser 0 ou 2
                ELSEIF p_SalaOrigem = 0 AND p_SalaDestino = 0 AND p_Status NOT IN (0, 2) THEN
                    SELECT -1 AS Result;

                -- Regra de Corredores (Movimentação entre salas internas)
                ELSEIF p_SalaOrigem != 0 AND p_SalaDestino != 0 THEN

                    -- Verificar se existe corredor aberto entre as duas salas
                    SELECT COUNT(*) INTO v_CorredorExiste
                    FROM Corridor
                    WHERE IDSimulacao = v_IDSimulacao
                      AND ((RoomA = p_SalaOrigem AND RoomB = p_SalaDestino)
                           OR (RoomA = p_SalaDestino AND RoomB = p_SalaOrigem))
                      AND Fechado = FALSE;

                    IF v_CorredorExiste = 0 THEN
                        SELECT -1 AS Result; -- Corredor não existe ou está fechado
                    ELSE
                        -- Inserção válida (movimento entre salas internas)
                        INSERT INTO MedicoesPassagens (IDSimulacao, Hora, SalaOrigem, SalaDestino, Marsami, Status, MongoId)
                        VALUES (v_IDSimulacao, p_Hora, p_SalaOrigem, p_SalaDestino, p_Marsami, p_Status, p_MongoId);
                        SELECT 1 AS Result;
                    END IF;

                ELSE
                    -- Movimentos de entrada/saída (SalaOrigem = 0 ou SalaDestino = 0)

                    -- Verificar spawn duplicado (mesmo Marsami não pode entrar duas vezes)
                    IF p_SalaOrigem = 0 AND p_SalaDestino != 0 THEN
                        SELECT COUNT(*) INTO v_CountDupMovimento
                        FROM MedicoesPassagens
                        WHERE IDSimulacao = v_IDSimulacao
                          AND Marsami = p_Marsami
                          AND SalaOrigem = 0;

                        IF v_CountDupMovimento > 0 THEN
                            SELECT -1 AS Result;
                        ELSE
                            INSERT INTO MedicoesPassagens (IDSimulacao, Hora, SalaOrigem, SalaDestino, Marsami, Status, MongoId)
                            VALUES (v_IDSimulacao, p_Hora, p_SalaOrigem, p_SalaDestino, p_Marsami, p_Status, p_MongoId);
                            SELECT 1 AS Result;
                        END IF;
                    ELSE
                        -- Saída normal (SalaDestino = 0)
                        
                        -- Verificar spam de finalização (SalaOrigem=0, SalaDestino=0)
                        IF p_SalaOrigem = 0 AND p_SalaDestino = 0 THEN
                            SELECT COUNT(*) INTO v_CountDupMovimento
                            FROM MedicoesPassagens
                            WHERE IDSimulacao = v_IDSimulacao
                              AND Marsami = p_Marsami
                              AND SalaOrigem = 0
                              AND SalaDestino = 0;
                            
                            IF v_CountDupMovimento > 0 THEN
                                SELECT -1 AS Result; -- Já existe, ignorar spam
                            ELSE
                                INSERT INTO MedicoesPassagens (IDSimulacao, Hora, SalaOrigem, SalaDestino, Marsami, Status, MongoId)
                                VALUES (v_IDSimulacao, p_Hora, p_SalaOrigem, p_SalaDestino, p_Marsami, p_Status, p_MongoId);
                                SELECT 1 AS Result;
                            END IF;
                        ELSE
                            -- Saída normal de uma sala para fora (SalaDestino = 0)
                            INSERT INTO MedicoesPassagens (IDSimulacao, Hora, SalaOrigem, SalaDestino, Marsami, Status, MongoId)
                            VALUES (v_IDSimulacao, p_Hora, p_SalaOrigem, p_SalaDestino, p_Marsami, p_Status, p_MongoId);
                            SELECT 1 AS Result;
                        END IF;
                    END IF;

                END IF;
            END IF;
        END IF;
    END IF;
END$$

DELIMITER ;

DELIMITER $$

CREATE PROCEDURE Inserir_Som(
    IN p_MongoId INT,
    IN p_Hora TIMESTAMP,
    IN p_Som DECIMAL(6,2)
)
BEGIN
    -- 1. DECLARAÇÃO DE VARIÁVEIS (Sempre no topo)
    DECLARE v_IDSimulacao INT;
    DECLARE v_CountMongo INT;

    -- 2. DECLARAÇÃO DE HANDLERS (Depois das variáveis)
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        -- Retorna 0 em caso de erro técnico/crítico no MySQL
        SELECT 0 AS Result;
    END;

    -- 3. LÓGICA DA PROCEDURE

    -- Verificar se o MongoID é nulo (Dado Inválido)
    IF p_MongoId IS NULL THEN
        SELECT -1 AS Result;

    ELSE
        -- Verificar se o MongoID já existe (Duplicado)
        SELECT COUNT(*) INTO v_CountMongo FROM Som WHERE MongoId = p_MongoId;

        IF v_CountMongo > 0 THEN
            SELECT -2 AS Result;

        ELSE
            -- Obter Simulação Ativa
            SELECT IDSimulacao INTO v_IDSimulacao
            FROM Simulacao
            WHERE Ativo = TRUE
            LIMIT 1;

            -- Validações de "Dado Inválido" (-1)
            -- - Som não pode ser negativo
            -- - Deve haver uma simulação ativa
            -- - A data não pode ser futura
            IF v_IDSimulacao IS NULL OR p_Som < 0 OR p_Hora > NOW() + INTERVAL 5 SECOND THEN
                SELECT -1 AS Result;

            ELSE
                -- Tentativa de Inserção
                INSERT INTO Som (IDSimulacao, Hora, Som, MongoId)
                VALUES (v_IDSimulacao, p_Hora, p_Som, p_MongoId);

                -- Se a inserção falhar sem erro crítico (ex: 0 linhas afetadas)
                IF ROW_COUNT() > 0 THEN
                    SELECT 1 AS Result;
                ELSE
                    SELECT 0 AS Result;
                END IF;
            END IF;
        END IF;
    END IF;
END$$

DELIMITER ;

DELIMITER $$

CREATE PROCEDURE Inserir_Temperatura(
    IN p_MongoId INT,
    IN p_Hora TIMESTAMP,
    IN p_Temperatura DECIMAL(6,2)
)
BEGIN
    -- 1. VARIÁVEIS PRIMEIRO
    DECLARE v_IDSimulacao INT;
    DECLARE v_ArCondicionado BOOLEAN;
    DECLARE v_UltimaTemp DECIMAL(6,2);
    DECLARE v_CountMongo INT;

    -- 2. HANDLERS DEPOIS DAS VARIÁVEIS
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        -- Retorna 0 em caso de erro técnico/crítico
        SELECT 0 AS Result;
    END;

    -- 3. LÓGICA DA PROCEDURE

    -- Verificar se o MongoID é nulo (Dado Inválido)
    IF p_MongoId IS NULL THEN
        SELECT -1 AS Result;

    ELSE
        -- Verificar se o MongoID já existe (Duplicado)
        SELECT COUNT(*) INTO v_CountMongo FROM Temperatura WHERE MongoId = p_MongoId;

        IF v_CountMongo > 0 THEN
            SELECT -2 AS Result;

        ELSE
            -- Obter Simulação Ativa
            SELECT IDSimulacao, ArCondicionado INTO v_IDSimulacao, v_ArCondicionado
            FROM Simulacao
            WHERE Ativo = TRUE
            LIMIT 1;

            -- Se não houver simulação ativa ou data for futura (Dado Inválido)
            IF v_IDSimulacao IS NULL OR p_Hora > NOW() + INTERVAL 5 SECOND THEN
                SELECT -1 AS Result;

            ELSE
                -- Tentativa de Inserção (Removida a lógica de validação do AC para permitir dados com delay)
                INSERT INTO Temperatura (IDSimulacao, Hora, Temperatura, MongoId)
                VALUES (v_IDSimulacao, p_Hora, p_Temperatura, p_MongoId);
                SELECT 1 AS Result;
            END IF;
        END IF;
    END IF;
END$$

DELIMITER ;

DELIMITER $$

CREATE PROCEDURE Ler_Alertas(
    IN p_LastId INT
)
BEGIN

	-- 1. DECLARAÇÃO DE VARIÁVEIS
    DECLARE v_IDSimulacao INT;
    DECLARE v_CurrentId INT;

    -- 2. HANDLER PARA ERROS TÉCNICOS (Retorna 0)
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SELECT 0 AS Result;
    END;

    -- 3. VERIFICAR SE EXISTE UMA SIMULAÇÃO ATIVA
    SELECT IDSimulacao INTO v_IDSimulacao
    FROM Simulacao
    WHERE Ativo = TRUE
    LIMIT 1;

    -- 4. PRÓXIMA MENSAGEM
    IF v_IDSimulacao IS NULL THEN
        -- Retorna -1: Não há jogo a decorrer
        SELECT -1 AS Result;

    ELSE
		SELECT *
        FROM Mensagens
        WHERE ID > p_LastId AND IDSimulacao = v_IDSimulacao
        ORDER BY ID ASC
        LIMIT 1;
    END IF;

END$$

DELIMITER ;

DELIMITER $$

CREATE PROCEDURE Remover_Utilizador(
    IN p_IDUtilizador INT
)
BEGIN
    DECLARE v_Email VARCHAR(50);

    -- Get email before deleting record
    SELECT Email INTO v_Email FROM Utilizador WHERE IDUtilizador = p_IDUtilizador;

    -- Check if user exists
    IF v_Email IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Utilizador não encontrado';
    END IF;

    -- Delete from table
    DELETE FROM Utilizador
    WHERE IDUtilizador = p_IDUtilizador;

    -- Drop MySQL User
    SET @sql_drop = CONCAT('DROP USER IF EXISTS ''', v_Email, '''@''%''');
    PREPARE stmt FROM @sql_drop;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;

END$$

DELIMITER ;

DELIMITER $$

CREATE PROCEDURE Ler_Leaderboard()
BEGIN
    SELECT 
        s.Equipa,
        s.IDSimulacao,
        s.Pontuacao,
        s.DataHoraInicio,
        (SELECT COUNT(*) FROM Mensagens m WHERE m.IDSimulacao = s.IDSimulacao) AS TotalAlertas,
        (SELECT COUNT(*) FROM Corridor c WHERE c.IDSimulacao = s.IDSimulacao AND c.Fechado = TRUE) AS TotalCorredoresFechados,
        (SELECT ROUND(AVG(t.Temperatura), 2) FROM Temperatura t WHERE t.IDSimulacao = s.IDSimulacao) AS MediaTemperatura,
        (SELECT ROUND(AVG(so.Som), 2) FROM Som so WHERE so.IDSimulacao = s.IDSimulacao) AS MediaSom
    FROM Simulacao s
    WHERE s.Ativo = FALSE
    ORDER BY s.Pontuacao DESC;
END$$

DELIMITER ;
