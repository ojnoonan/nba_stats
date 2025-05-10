import tailwindcss from 'tailwindcss'
import autoprefixer from 'autoprefixer'
import postcssNesting from 'postcss-nesting'

/** @type {import('postcss').Config} */
export default {
  plugins: {
    'postcss-import': {},
    'postcss-nesting': {},
    'tailwindcss/nesting': {},
    tailwindcss: {},
    autoprefixer: {},
  },
}