# ==================== TAB 4 - Controle de Estoque ====================
with tab4:
    st.subheader("📦 Controle de Estoque Interno")

    # --- Criar ou carregar estoque interno ---
    if "df_estoque" not in st.session_state:
        st.session_state.df_estoque = pd.DataFrame(columns=["Produto", "SKU", "Quantidade", "Estoque Mínimo"])

    df_estoque = st.session_state.df_estoque

    # --- Formulário para adicionar/editar produtos ---
    st.markdown("### ➕ Adicionar / Atualizar Produto")
    with st.form("form_estoque", clear_on_submit=True):
        produto = st.text_input("Produto")
        sku = st.text_input("SKU")
        quantidade = st.number_input("Quantidade", min_value=0, value=0)
        estoque_minimo = st.number_input("Estoque Mínimo", min_value=0, value=0)
        submit = st.form_submit_button("Adicionar / Atualizar")

        if submit:
            if produto.strip() == "" or sku.strip() == "":
                st.error("Preencha Produto e SKU!")
            else:
                # Atualizar se SKU já existe
                if sku in df_estoque["SKU"].values:
                    df_estoque.loc[df_estoque["SKU"] == sku, ["Produto", "Quantidade", "Estoque Mínimo"]] = [produto, quantidade, estoque_minimo]
                    st.success(f"Produto {produto} atualizado!")
                else:
                    df_estoque = pd.concat([df_estoque, pd.DataFrame([{
                        "Produto": produto,
                        "SKU": sku,
                        "Quantidade": quantidade,
                        "Estoque Mínimo": estoque_minimo
                    }])], ignore_index=True)
                    st.success(f"Produto {produto} adicionado!")

                st.session_state.df_estoque = df_estoque

    # --- Excluir produto ---
    if not df_estoque.empty:
        st.markdown("### ❌ Excluir Produto")
        sku_excluir = st.selectbox("Selecione o SKU do produto para excluir", df_estoque["SKU"])
        if st.button("Excluir Produto"):
            st.session_state.df_estoque = df_estoque[df_estoque["SKU"] != sku_excluir].reset_index(drop=True)
            st.success(f"Produto com SKU {sku_excluir} excluído!")
            df_estoque = st.session_state.df_estoque  # Atualiza dataframe local

    # --- Alerta de estoque baixo ---
    estoque_baixo = df_estoque[df_estoque["Quantidade"] <= df_estoque["Estoque Mínimo"]]
    if not estoque_baixo.empty:
        st.warning("⚠️ Produtos com estoque baixo!")
        st.dataframe(estoque_baixo)

    # --- Tabela completa de estoque ---
    st.subheader("📝 Estoque Atual")
    st.dataframe(df_estoque)

    # --- Gráfico de barras quantidade vs estoque mínimo ---
    st.subheader("📊 Estoque Atual x Estoque Mínimo")
    if not df_estoque.empty:
        fig_estoque = px.bar(
            df_estoque,
            x="Produto",
            y=["Quantidade", "Estoque Mínimo"],
            barmode="group",
            color_discrete_sequence=["#1f77b4", "#ff7f0e"],
            text_auto=True,
            title="Quantidade em Estoque vs Estoque Mínimo"
        )
        st.plotly_chart(fig_estoque, use_container_width=True)
