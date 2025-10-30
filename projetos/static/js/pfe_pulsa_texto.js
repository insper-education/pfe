// ------- RECURSO PARA DAR FEEDBACK   -------/////
function pulsa_texto(atualizado, id) {
    // Verifica se o DIV já existe
    var f = document.getElementById(id);
    if (!f) {
        // Cria o DIV se não existir
        f = document.createElement('div');
        f.id = id;
        f.style.color = "white";
        f.style.position = "fixed"; // Fixo na tela
        f.style.top = "10px"; // Distância do topo
        f.style.left = "50%"; // Centraliza horizontalmente
        f.style.transform = "translateX(-50%)"; // Ajusta a posição para centralizar
        f.style.borderRadius = "4px"; // Bordas arredondadas
        f.style.padding = "10px"; // Espaçamento interno
        f.style.zIndex = "1000"; // Garante que fique acima de outros elementos
        f.style.transition = "opacity 0.5s"; // Transição suave
        document.body.appendChild(f); // Adiciona o DIV ao corpo do documento
    }

    // Atualiza o conteúdo e a cor de fundo
    if (atualizado) {
        f.innerHTML = "Valores atualizados no servidor.";
        f.style.backgroundColor = "green";
    } else {
        f.innerHTML = "Erro ao atualizar dados no servidor.";
        f.style.backgroundColor = "red";
    }

    // Exibe o DIV
    f.style.display = '';
    
    // Oculta após 2 segundos
    setTimeout(function() {
        f.style.display = 'none';
    }, 2000);
}
