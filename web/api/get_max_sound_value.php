<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);
header('Content-Type: application/json');

$response = array('success' => false, 'message' => '', 'data' => null);

$username = $_REQUEST['username'] ?? '';
$password = $_REQUEST['password'] ?? '';
$database = $_REQUEST['database'] ?? '';

if (empty($username) || empty($password) || empty($database)) {
    $response['message'] = 'Preencha todos os campos.';
    echo json_encode($response);
    exit;
}

$host = 'mysql';
$conn = new mysqli($host, $username, $password, $database);

if ($conn->connect_error) {
    $response['message'] = "Erro de conexão: " . $conn->connect_error;
    echo json_encode($response);
    exit;
}

$sql = "SELECT 
    (sm.NormalNoise + sm.NoiseVarToleration) AS maximo,
    cj.alerta_som AS offset
FROM SetupMaze sm
JOIN ConfigJogo cj ON sm.IDSimulacao = cj.IDSimulacao
WHERE sm.IDSimulacao = (SELECT IDSimulacao FROM Simulacao ORDER BY Ativo DESC, IDSimulacao DESC LIMIT 1)
LIMIT 1
";

$result = $conn->query($sql);

if ($result) {
    $row = $result->fetch_assoc();
    if ($row) {
        $response['success'] = true;
        $response['data'] = array(
            "maximo" => (float) $row['maximo'],
            "offset" => (float) $row['offset']
        );
        $response['message'] = 'Configuração de som carregada com offset.';
    } else {
        $response['message'] = 'Nenhuma configuração de som encontrada.';
    }
} else {
    $response['message'] = "Erro na query: " . $conn->error;
}

$conn->close();
echo json_encode($response);
?>