module.exports = {
    content: [
        '../../esp_generica/*.{html,js,py}',
        '../../esp_generica/templates/*.{html,js,py}',
        '../../esp_generica/forms.py',
        '../../embeddings/templates/*.{html,js,py}',
        '../../embeddings/forms.py',
    ],
    safelist: [
        'bg-blue-600',
        'bg-green-600',
        'bg-red-600',
        'bg-purple-600',
        'bg-indigo-600',
        'bg-teal-600',
        'text-blue-600',
        'text-green-600',
        'text-red-600',
        'text-purple-600',
        'text-indigo-600',
        'text-teal-600',

        'input',
        'bg-yellow-500',
    ],
}
