const path = require("path")
const {VueLoaderPlugin} = require("vue-loader")
module.exports = {
    watch: false,
    mode: "development",
    entry: path.join(__dirname, "./src/main.ts"),
    module: {
        rules: [
            {
                test: /\.vue$/,
                use: "vue-loader",
            },
            {
                test: /\.css$/,
                use: ["vue-style-loader", "css-loader"]
            },
            {
                test: /\.ts$/,
                loader: 'ts-loader',
                options: { appendTsSuffixTo: [/\.vue$/] }
            }
        ]
    },
    output: {
        path: path.join(__dirname, "./dist"),
        filename:"bundle.js"
    },
    resolve: {
        extensions: ['.ts', '.js'],
    },
    plugins: [
        new VueLoaderPlugin()
    ]
}