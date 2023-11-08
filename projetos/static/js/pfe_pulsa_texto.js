// ------- RECURSO PARA DAR FEEDBACK   -------/////
function pulsa_texto(atualizado, id) {
    var f = document.getElementById(id);
    f.style.color = "white";
    if(atualizado) {
        f.innerHTML = "Valores atualizados no servidor.";
        f.style.backgroundColor = "green";
    } else {
        f.innerHTML = "Erro ao atualizar dados no servidor.";
        f.style.backgroundColor = "red";
    }
    f.style.display = '';
    setTimeout(function() {f.style.display = 'none';}, 2000);
}