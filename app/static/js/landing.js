const socket = io.connect('http://' + document.domain + ':' + location.port, {
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000
});
const isLoggedIn = document.documentElement.getAttribute('data-logged-in') === 'true';

// Função para criar um card de produto
function createProductCard(produto) {
    const newCard = document.createElement('div');
    newCard.className = 'product-card';
    newCard.setAttribute('data-product-id', produto.produto_id || produto.id);
    
    newCard.innerHTML = `
        <img src="${produto.imagem}" alt="${produto.nome}">
        <h3>${produto.nome}</h3>
        <p class="price">R$ ${Number(produto.preco).toFixed(2)}</p>
        <p class="stock">${produto.estoque} em estoque</p>
        <button class="add-to-cart" onclick="addToCart(${produto.produto_id || produto.id})" ${produto.estoque <= 0 ? 'disabled' : ''}>
            ${produto.estoque <= 0 ? 'Sem Estoque' : 'Adicionar'}
        </button>
    `;
    
    return newCard;
}

// Carregar produtos iniciais
function loadInitialProducts() {
    const productGrid = document.querySelector('.product-grid');
    const produtos = Array.from(productGrid.children);
    
    // Limpa o grid e recria os cards para garantir consistência
    productGrid.innerHTML = '';
    produtos.forEach(produto => {
        const produtoData = {
            id: produto.dataset.productId,
            nome: produto.querySelector('h3').textContent,
            preco: parseFloat(produto.querySelector('.price').textContent.replace('R$ ', '')),
            estoque: parseInt(produto.querySelector('.stock').textContent),
            imagem: produto.querySelector('img').src
        };
        
        if (produtoData.estoque > 0) {
            productGrid.appendChild(createProductCard(produtoData));
        }
    });
}

// Carregar produtos quando a página carregar e quando reconectar
document.addEventListener('DOMContentLoaded', loadInitialProducts);
socket.on('connect', loadInitialProducts);

// Adicionar handlers de conexão
socket.on('connect', () => {
    console.log('Conectado ao servidor WebSocket');
});

socket.on('disconnect', () => {
    console.log('Desconectado do servidor WebSocket');
});

socket.on('connect_error', (error) => {
    console.error('Erro de conexão WebSocket:', error);
});

// Atualização em tempo real do estoque
socket.on('estoque_atualizado', (data) => {
    const productCard = document.querySelector(`.product-card[data-product-id="${data.produto_id}"]`);
    if (productCard) {
        const stockElement = productCard.querySelector('.stock');
        const button = productCard.querySelector('button');
        if (stockElement) {
            stockElement.textContent = `${data.estoque} em estoque`;
            
            // Atualiza o botão baseado no estoque
            button.disabled = data.estoque <= 0;
            button.textContent = data.estoque <= 0 ? 'Sem Estoque' : 'Adicionar';
        }
        
        // Remove o card se não houver estoque
        if (data.estoque <= 0) {
            productCard.remove();
        }
    }
});

// Atualização quando um produto é removido
socket.on('produto_removido', (data) => {
    const productCard = document.querySelector(`.product-card[data-product-id="${data.produto_id}"]`);
    if (productCard) {
        productCard.remove();
    }
});

// Novo evento para quando um produto é adicionado
socket.on('produto_adicionado', (data) => {
    const productGrid = document.querySelector('.product-grid');
    if (productGrid && data.estoque > 0) {
        productGrid.appendChild(createProductCard(data));
    }
});

// Atualização quando um produto é editado
socket.on('produto_atualizado', (data) => {
    let productCard = document.querySelector(`.product-card[data-product-id="${data.produto_id}"]`);
    
    // Se o produto não existe no DOM e tem estoque, cria um novo card
    if (!productCard && data.estoque > 0) {
        const productGrid = document.querySelector('.product-grid');
        productGrid.appendChild(createProductCard(data));
        return;
    }
    
    // Se existe o card
    if (productCard) {
        // Se o estoque for 0, remove o card
        if (data.estoque <= 0) {
            productCard.remove();
            return;
        }
        
        // Atualiza as informações do card existente
        productCard.querySelector('img').src = data.imagem;
        productCard.querySelector('h3').textContent = data.nome;
        productCard.querySelector('.price').textContent = `R$ ${Number(data.preco).toFixed(2)}`;
        productCard.querySelector('.stock').textContent = `${data.estoque} em estoque`;
        
        const button = productCard.querySelector('button');
        if (button) {
            button.disabled = data.estoque <= 0;
            button.textContent = data.estoque <= 0 ? 'Sem Estoque' : 'Adicionar';
        }
    }
});

// Função para atualizar o contador do carrinho
function updateCartCounter() {
    const counter = document.querySelector('.cart-counter');
    if (!counter) return;

    // Pegar o valor atual e incrementar
    let currentCount = parseInt(counter.textContent || '0');
    currentCount++;

    // Atualizar o contador
    counter.textContent = currentCount;
    counter.style.display = currentCount > 0 ? 'flex' : 'none';
}

function addToCart(productId) {
    if (!isLoggedIn) {
        const feedback = document.createElement('div');
        feedback.className = 'feedback';
        feedback.textContent = 'Por favor, faça login ou crie uma conta para adicionar produtos ao carrinho';
        document.body.appendChild(feedback);

        setTimeout(() => {
            feedback.remove();
        }, 3000);
        return;
    }

    fetch(`/add_to_cart/${productId}`, { method: 'POST' })
        .then(response => {
            if (response.ok) {
                updateCartCounter();
            } else {
                console.error("Erro ao adicionar ao carrinho");
            }
        });
}

// Inicializar o contador do carrinho quando a página carregar
document.addEventListener('DOMContentLoaded', () => {
    // ... existing DOMContentLoaded code ...

    // Inicializar o contador do carrinho
    const counter = document.querySelector('.cart-counter');
    if (counter) {
        fetch('/get_cart_count')
            .then(response => response.json())
            .then(data => {
                counter.textContent = data.count;
                counter.style.display = data.count > 0 ? 'flex' : 'none';
            });
    }

    // Adiciona handler para o link de logout
    const logoutLink = document.querySelector('a[href="/logout"]');
    if (logoutLink) {
        logoutLink.addEventListener('click', handleLogout);
    }
});

// Adicione esta função no início do arquivo, junto com as outras funções
function handleLogout(event) {
    event.preventDefault();
    const logoutUrl = event.currentTarget.href;
    
    fetch(logoutUrl)
        .then(() => {
            window.location.reload();  // Recarrega a página após o logout
        })
        .catch(error => {
            console.error('Erro ao fazer logout:', error);
        });
}
