<?php
session_start();
require_once 'db.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = $_POST['email'];
    $password = $_POST['password'] ?? '';
    
    // Check if user exists in Utilizador table using root connection
    $stmt = $pdo->prepare('SELECT * FROM Utilizador WHERE Email = ?');
    $stmt->execute([$email]);
    $user = $stmt->fetch();
    
    if ($user) {
        // Verify password by attempting to connect to MySQL as the user
        try {
            $host = (strtoupper(substr(PHP_OS, 0, 3)) === 'WIN') ? '127.0.0.1' : 'mysql';
            $test_pdo = new PDO("mysql:host=$host;dbname=bd_pisid;charset=utf8mb4", $email, $password, [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION
            ]);
            
            $_SESSION['user_id'] = $user['IDUtilizador'];
            $_SESSION['nome'] = $user['Nome'];
            $_SESSION['tipo'] = $user['Tipo'];
            $_SESSION['email'] = $user['Email'];
            $_SESSION['equipa'] = $user['Equipa'];
            $_SESSION['mysql_pass'] = $password; // Guardamos a password em sessão para uso posterior
            
            header('Location: dashboard.php');
            exit;
        } catch (\PDOException $e) {
            $error = "Password incorreta ou falha de autenticação MySQL.";
        }
    } else {
        $error = "Utilizador não encontrado.";
    }
}
?>
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <title>PISID - Login</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <div class="container auth-container">
        <div class="glass-panel">
            <h2>Bem-vindo</h2>
            <?php if (isset($error)): ?>
                <div class="alert alert-error"><?= htmlspecialchars($error) ?></div>
            <?php endif; ?>
            <form method="POST">
                <div class="form-group">
                    <label>Email do Utilizador</label>
                    <input type="email" name="email" required placeholder="Insira o seu email">
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" name="password" required placeholder="Insira a sua password">
                </div>
                <button type="submit" class="btn">Entrar</button>
            </form>
        </div>
    </div>
</body>
</html>
