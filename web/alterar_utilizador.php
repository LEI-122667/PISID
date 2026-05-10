<?php
session_start();
require_once 'db.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: index.php');
    exit;
}

$current_user_id = $_SESSION['user_id'];
$current_user_tipo = $_SESSION['tipo'];

// Target user ID (either from GET if admin, or current user)
$target_user_id = (isset($_GET['id']) && $current_user_tipo === 'Admin') ? (int) $_GET['id'] : $current_user_id;

// Get target user data
$stmt = $pdo->prepare("SELECT * FROM Utilizador WHERE IDUtilizador = ?");
$stmt->execute([$target_user_id]);
$user = $stmt->fetch();

if (!$user) {
    die("Utilizador não encontrado.");
}

$is_admin_editing_others = ($current_user_tipo === 'Admin' && $target_user_id != $current_user_id);

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $nome = $_POST['nome'];
    $telemovel = $_POST['telemovel'];
    $email = $_POST['email'];
    $dataNasc = $_POST['data_nascimento'] ?: null;
    $tipo = $is_admin_editing_others ? $_POST['tipo'] : $user['Tipo'];
    $equipa = $is_admin_editing_others ? ($_POST['equipa'] ?: null) : $user['Equipa'];

    try {
        if ($current_user_tipo === 'Admin') {
            $stmt = $pdo->prepare("CALL Admin_Alterar_Utilizador(?, ?, ?, ?, ?, ?, ?)");
            $stmt->execute([$target_user_id, $nome, $tipo, $email, $telemovel, $dataNasc, $equipa]);
        } else {
            // Criar uma ligação temporária como o próprio utilizador para satisfazer a função USER() da SP
            $host = (strtoupper(substr(PHP_OS, 0, 3)) === 'WIN') ? '127.0.0.1' : 'mysql';
            $user_pdo = new PDO("mysql:host=$host;dbname=bd_pisid;charset=utf8mb4", $_SESSION['email'], $_SESSION['mysql_pass'], [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION
            ]);
            $stmt = $user_pdo->prepare("CALL Alterar_Utilizador(?, ?, ?, ?)");
            $stmt->execute([$nome, $telemovel, $email, $dataNasc]);
        }

        if ($target_user_id == $current_user_id) {
            $_SESSION['nome'] = $nome;
            $_SESSION['email'] = $email;
        }

        $success = "Dados atualizados com sucesso!";

        // Refresh data
        $stmt = $pdo->prepare("SELECT * FROM Utilizador WHERE IDUtilizador = ?");
        $stmt->execute([$target_user_id]);
        $user = $stmt->fetch();

    } catch (\PDOException $e) {
        $error = "Erro: " . $e->getMessage();
    }
}
?>
<!DOCTYPE html>
<html lang="pt">

<head>
    <meta charset="UTF-8">
    <title>Alterar Utilizador</title>
    <link rel="stylesheet" href="css/style.css">
</head>

<body>
    <div class="nav-bar">
        <h3>PISID</h3>
        <div class="nav-links">
            <a href="<?= $is_admin_editing_others ? 'gerir_utilizadores.php' : 'dashboard.php' ?>">Voltar</a>
        </div>
    </div>
    <div class="container">
        <div class="glass-panel" style="max-width: 600px; margin: 0 auto;">
            <h2><?= $is_admin_editing_others ? 'Alterar Utilizador #' . $target_user_id : 'Alterar Perfil' ?></h2>

            <?php if (isset($error)): ?>
                <div class="alert alert-error"><?= htmlspecialchars($error) ?></div>
            <?php endif; ?>
            <?php if (isset($success)): ?>
                <div class="alert alert-success"><?= htmlspecialchars($success) ?></div>
            <?php endif; ?>

            <form method="POST">
                <div class="form-group">
                    <label>Nome</label>
                    <input type="text" name="nome" value="<?= htmlspecialchars($user['Nome']) ?>" required>
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" name="email" value="<?= htmlspecialchars($user['Email']) ?>" required>
                </div>
                <div class="form-group">
                    <label>Telemóvel</label>
                    <input type="text" name="telemovel" value="<?= htmlspecialchars($user['Telemovel'] ?? '') ?>">
                </div>
                <div class="form-group">
                    <label>Data de Nascimento</label>
                    <input type="date" name="data_nascimento"
                        value="<?= htmlspecialchars($user['DataNascimento'] ?? '') ?>">
                </div>

                <?php if ($is_admin_editing_others): ?>
                    <div class="form-group">
                        <label>Tipo</label>
                        <select name="tipo" required>
                            <option value="Admin" <?= $user['Tipo'] === 'Admin' ? 'selected' : '' ?>>Admin</option>
                            <option value="User" <?= $user['Tipo'] === 'User' ? 'selected' : '' ?>>User</option>
                            <option value="Android" <?= $user['Tipo'] === 'Android' ? 'selected' : '' ?>>Android</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Equipa (ID)</label>
                        <input type="number" name="equipa" value="<?= htmlspecialchars($user['Equipa'] ?? '') ?>">
                    </div>
                <?php endif; ?>

                <button type="submit" class="btn">Atualizar Dados</button>
            </form>

            <?php if (!$is_admin_editing_others): ?>
                <div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.1);">
                    <p style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 1rem;">Zona de Perigo: Esta
                        ação é permanente.</p>
                    <a href="remover_utilizador.php?id=<?= $target_user_id ?>" class="btn btn-secondary"
                        style="background: #ff4757; width: auto;"
                        onclick="return (confirm('Tem a CERTEZA que deseja eliminar a sua conta permanentemente?') && confirm('Esta ação não pode ser desfeita. Deseja mesmo continuar?'))">
                        Eliminar Minha Conta
                    </a>
                </div>
            <?php endif; ?>
        </div>
    </div>
</body>

</html>