<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);
header('Content-Type: application/json');

$response = array('success' => false, 'message' => '', 'data' => null);

$username = $_REQUEST['username'] ?? '';
$password = $_REQUEST['password'] ?? '';
$database = $_REQUEST['database'] ?? '';

$host = 'mysql'; 

$conn = new mysqli($host, $username, $password, $database);

if ($conn->connect_error) {
    $response['message'] = "Erro de ligação: " . $conn->connect_error;
    echo json_encode($response);
    exit;
}

$sql = "SELECT 
    (sm.NormalTemperature - sm.TemperatureVarLowToleration) AS minimo,
    (sm.NormalTemperature + sm.TemperatureVarHighToleration) AS maximo,
    cj.alerta_temperatura_low AS offset_min,
    cj.alerta_temperatura_high AS offset_max
FROM SetupMaze sm
JOIN ConfigJogo cj ON sm.IDSimulacao = cj.IDSimulacao
WHERE sm.IDSimulacao = (SELECT IDSimulacao FROM Simulacao WHERE Ativo = TRUE LIMIT 1)
LIMIT 1
";

$result = $conn->query($sql);

if ($result && $row = $result->fetch_assoc()) {
    $response['success'] = true;
    $response['data'] = array(
        "minimo" => (float) $row['minimo'],
        "maximo" => (float) $row['maximo'],
        "offset_min" => (float) $row['offset_min'],
        "offset_max" => (float) $row['offset_max']
    );
} else {
    $response['message'] = "Não foram encontrados limites na tabela.";
}

$conn->close();
echo json_encode($response);
?>