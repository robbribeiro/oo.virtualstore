const socket = io.connect('http://' + document.domain + ':' + location.port);
const fileInput = document.getElementById('file-input');
const fileChosen = document.getElementById('file-chosen');
const previewImg = document.getElementById('preview-img');

// Atualização em tempo real do estoque
socket.on('estoque_atualizado', (data) => {
    const productCard = document.querySelector(`.single-card[data-product-id="${data.produto_id}"] .stock`);
    if (productCard) {
        productCard.textContent = `Estoque: ${data.estoque}`;
    }
});

// Atualização em tempo real quando um produto é editado
socket.on('produto_atualizado', (data) => {
    const productCard = document.querySelector(`.single-card[data-product-id="${data.produto_id}"]`);
    if (productCard) {
        productCard.querySelector('h3').textContent = data.nome;
        productCard.querySelector('.price').textContent = `R$${data.preco.toFixed(2)}`;
        productCard.querySelector('.stock').textContent = `Estoque: ${data.estoque}`;
        productCard.querySelector('img').src = data.imagem;
    }
});

// Atualização em tempo real quando um produto é removido
socket.on('produto_removido', (data) => {
    const productCard = document.querySelector(`.single-card[data-product-id="${data.produto_id}"]`);
    if (productCard) {
        productCard.remove();
    }
});

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
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'  // Importante para enviar cookies de sessão
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                const productCard = document.querySelector(`.single-card[data-product-id="${productId}"]`);
                if (productCard) {
                    productCard.remove();
                }
            } else {
                throw new Error(data.message || "Erro desconhecido");
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            alert(error.message || "Erro ao excluir o produto!");
        });
    }
}

// Adicionar produto via AJAX
document.getElementById('addProductForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    fetch('/admin/add_product', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else {
            alert(data.message || "Erro ao adicionar produto!");
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        alert("Erro ao adicionar produto!");
    });
});