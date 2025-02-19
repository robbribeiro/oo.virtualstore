const socket = io.connect('http://' + document.domain + ':' + location.port);
const fileInput = document.getElementById('file-input');
const fileChosen = document.getElementById('file-chosen');
const previewImg = document.getElementById('preview-img');

fileInput.addEventListener('change', function () {
    const file = this.files[0];

    if (file) {
        // Verifica se o arquivo é um PNG, JPG ou JPEG
        const validTypes = ['image/png', 'image/jpg', 'image/jpeg'];
        if (!validTypes.includes(file.type)) {
            alert('Arquivo inválido! Por favor, envie uma imagem no formato PNG, JPG ou JPEG.');
            fileInput.value = ''; // Limpa o input para forçar uma nova seleção válida
            fileChosen.textContent = 'Nenhum arquivo foi selecionado';
            previewImg.hidden = true; // Esconde o preview
            return; // Sai da função sem processar
        }
        // Atualiza o texto com o nome do arquivo
        fileChosen.textContent = file.name;

        // Cria um objeto URL para mostrar o preview da imagem
        const reader = new FileReader();
        reader.onload = function (e) {
            previewImg.src = e.target.result;
            previewImg.hidden = false; // Mostra a imagem
        };
        reader.readAsDataURL(file);
    } else {
        fileChosen.textContent = 'Nenhum arquivo foi selecionado';
        previewImg.hidden = true; // Esconde a imagem caso não haja arquivo
    }
});

function deleteProduct(productId) {
    if (confirm('Tem certeza que deseja excluir este produto?')) {
        fetch(`/admin/delete_product/${productId}`, {
            method: 'POST'
        }).then(response => {
            if (response.ok) {
                location.reload();
            } else {
                alert("Erro ao excluir o produto!");
            }
        });
    }
}

// Atualizar estoque em tempo real
socket.on('estoque_atualizado', (data) => {
    const estoqueElement = document.querySelector(`.product-item[data-id="${data.produto_id}"] .estoque`);
    if (estoqueElement) {
        estoqueElement.textContent = data.estoque;
    }
});

// Adicionar produto via AJAX
document.getElementById('addProductForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    fetch('/admin/add_product', {
        method: 'POST',
        body: formData
    }).then(response => response.json())
      .then(data => {
          if (data.success) {
              location.reload();
          }
      });
});