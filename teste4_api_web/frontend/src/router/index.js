import { createRouter, createWebHistory } from "vue-router";
import Listagem from "../views/Listagem.vue";
import Detalhe from "../views/Detalhe.vue";

const routes = [
  { path: "/", name: "Listagem", component: Listagem },
  { path: "/operadora/:cnpj", name: "Detalhe", component: Detalhe, props: true },
];

export default createRouter({
  history: createWebHistory(),
  routes,
});
