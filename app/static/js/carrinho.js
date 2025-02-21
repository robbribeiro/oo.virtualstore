const socket = io();

socket.on('carrinho_atualizado', function(data) {
    const item = document.querySelector(`.cart-item[data-product-id="${data.produto_id}"]`);
    if (item) {
        const quantityDisplay = item.querySelector('.quantity-display');
        quantityDisplay.textContent = data.quantidade;
        
        // Se a quantidade for 0, remove o item
        if (data.quantidade <= 0) {
            item.remove();
            // Se não houver mais itens, recarrega a página
            if (document.querySelectorAll('.cart-item').length === 0) {
                window.location.reload();
            }
        }
        
        // Atualiza o total
        atualizarTotal();
    }
});

socket.on('estoque_atualizado', function(data) {
    // Atualiza o estoque na página de produtos se estiver aberta
    const productCard = document.querySelector(`.product-card[data-product-id="${data.produto_id}"]`);
    if (productCard) {
        const stockElement = productCard.querySelector('.stock');
        stockElement.textContent = `${data.estoque} em estoque`;
    }
});

function removerDoCarrinho(productId) {
    fetch(`/remove_from_cart/${productId}`, { 
        method: 'POST' 
    })
    .then(response => {
        if (response.ok) {
            const item = document.querySelector(`.cart-item[data-product-id="${productId}"]`);
            if (item) {
                item.remove();
                atualizarTotal();
                
                // Se não houver mais itens, recarrega a página
                if (document.querySelectorAll('.cart-item').length === 0) {
                    window.location.reload();
                }
            }
        } else {
            alert("Erro ao remover item do carrinho!");
        }
    });
}

function atualizarTotal() {
    fetch('/get_cart_total')
        .then(response => response.json())
        .then(data => {
            const totalElement = document.querySelector('.cart-summary h3');
            if (totalElement) {
                totalElement.textContent = `Total: R$ ${data.total.toFixed(2)}`;
            }
        });
}

function finalizarCompra() {
    fetch('/finalizar_compra', { method: 'POST' })
        .then(response => {
            if (response.ok) {
                alert("Compra finalizada com sucesso!");
                window.location.href = '/';
            } else {
                alert("Erro ao finalizar a compra!");
            }
        });
}

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

document.addEventListener('DOMContentLoaded', () => {
    // Adiciona handler para o link de logout
    const logoutLink = document.querySelector('a[href="/logout"]');
    if (logoutLink) {
        logoutLink.addEventListener('click', handleLogout);
    }
});