const fileInput = document.getElementById('file-input');
const fileChosen = document.getElementById('file-chosen');
const previewImg = document.getElementById('preview-img');
const currentImg = document.getElementById('current-img'); // Referência à imagem atual
    
fileInput.addEventListener('change', function () {
    const file = this.files[0];
    
    if (file) {
        // Verifica se o arquivo é um PNG, JPG ou JPEG
        const validTypes = ['image/png', 'image/jpg', 'image/jpeg'];
        if (!validTypes.includes(file.type)) {
        alert('Arquivo inválido! Por favor, envie uma imagem no formato PNG, JPG ou JPEG.');
        fileInput.value = ''; // Limpa o input para forçar uma nova seleção válida
        fileChosen.textContent = 'Nenhum arquivo foi selecionado';
        previewImg.hidden = true;
        currentImg.hidden = false;
        return;
        }

        // Atualiza o texto com o nome do arquivo
        fileChosen.textContent = file.name;
    
        // Cria um objeto URL para mostrar o preview da imagem
        const reader = new FileReader();
        reader.onload = function (e) {
            previewImg.src = e.target.result;
            previewImg.hidden = false; // Mostra o preview
            currentImg.hidden = true; // Esconde a imagem atual
        };
        reader.readAsDataURL(file);
    } else {
        fileChosen.textContent = 'Nenhum arquivo foi selecionado';
        previewImg.hidden = true; // Esconde o preview
        currentImg.hidden = false; // Mostra a imagem atual novamente
    }
});