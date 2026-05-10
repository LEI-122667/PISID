<?php
session_start();
require_once 'db.php';

$id_remover = $_GET['id'] ?? null;

// Permissões:
// 1. Admins podem remover qualquer um (exceto eles próprios neste script para segurança)
// 2. Utilizadores normais podem remover apenas a sua própria conta
$can_remove = false;
if ($_SESSION['tipo'] === 'Admin') {
    if ($id_remover != $_SESSION['user_id']) {
        $can_remove = true;
    } else {
        header('Location: gerir_utilizadores.php?error=Como admin, deve pedir a outro admin para remover a sua conta ou usar o DB.');
        exit;
    }
} else {
    if ($id_remover == $_SESSION['user_id']) {
        $can_remove = true;
    } else {
        header('Location: dashboard.php?error=Acesso negado. Apenas pode remover a sua própria conta.');
        exit;
    }
}

if ($can_remove && $id_remover) {
    try {
        $stmt = $pdo->prepare("CALL Remover_Utilizador(?)");
        $stmt->execute([$id_remover]);
        
        // Se o utilizador removeu a sua própria conta, fazemos logout
        if ($id_remover == $_SESSION['user_id']) {
            session_destroy();
            header('Location: index.php?success=A sua conta foi eliminada permanentemente.');
            exit;
        }

        header('Location: gerir_utilizadores.php?success=Utilizador removido com sucesso.');
    } catch (\PDOException $e) {
        $redirect = ($_SESSION['tipo'] === 'Admin') ? 'gerir_utilizadores.php' : 'alterar_utilizador.php';
        header("Location: $redirect?error=Erro ao remover conta: " . $e->getMessage());
    }
} else {
    header('Location: gerir_utilizadores.php');
}
exit;
