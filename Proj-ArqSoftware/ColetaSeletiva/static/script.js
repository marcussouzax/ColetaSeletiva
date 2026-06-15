async function cadastrarUsuario() {
    const nome = document.getElementById("usuario-nome").value;
    const email = document.getElementById("usuario-email").value;
    const senha = document.getElementById("usuario-senha").value;

    await fetch("/api/usuarios/registrar", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({nome, email, senha})
    });

    alert("Usuário cadastrado!");
    atualizarStats();
}

async function carregarPontos() {
    const res = await fetch("/api/pontos");
    const data = await res.json();

    const div = document.getElementById("lista-pontos");
    div.innerHTML = "";

    data.forEach(p => {
        div.innerHTML += `<div class="card">${p.nome} - ${p.endereco}</div>`;
    });
}

async function atualizarStats() {
    const res = await fetch("/api/stats");
    const data = await res.json();

    document.getElementById("total-usuarios").innerText = data.usuarios;
    document.getElementById("total-pontos").innerText = data.pontos;
    document.getElementById("total-coletas").innerText = data.coletas;
}

async function gerarRelatorio() {
    const res = await fetch("/api/relatorios");
    const data = await res.json();

    document.getElementById("relatorio-output").innerHTML = `
        <h2 style="color:#22c55e;">${data.titulo}</h2>
        <p>👤 Usuários: ${data.total_usuarios}</p>
        <p>📍 Pontos: ${data.total_pontos}</p>
        <p>🚛 Coletas: ${data.total_coletas}</p>

        <h3>Lista de usuários</h3>
        ${data.usuarios.map(u => `<p>${u.nome} - ${u.email}</p>`).join("")}
    `;
}

document.addEventListener("DOMContentLoaded", () => {
    atualizarStats();
    carregarPontos();
});