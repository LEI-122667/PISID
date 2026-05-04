<?php
session_start();
require_once 'db.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = $_POST['email'];
    
    $stmt = $pdo->prepare('SELECT * FROM Utilizador WHERE Email = ?');
    $stmt->execute([$email]);
    $user = $stmt->fetch();
    
    if ($user) {
        $_SESSION['user_id'] = $user['IDUtilizador'];
        $_SESSION['nome'] = $user['Nome'];
        $_SESSION['tipo'] = $user['Tipo'];
        $_SESSION['email'] = $user['Email'];
        $_SESSION['equipa'] = $user['Equipa'];
        $_SESSION['permissao_criar_jogo'] = $user['permissaoCriarJogo'];
        
        header('Location: dashboard.php');
        exit;
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
                <button type="submit" class="btn">Entrar</button>
            </form>
        </div>
    </div>
</body>
</html>
