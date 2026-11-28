/* Shared formative area grid, derived from F01's positive-area organizer.
 * Schematic only. Accessible mathematical equivalents remain in the page/table.
 * No network, session, bank, evaluation or mastery state.
 */
function renderStemAreaGrid(container, rows, visibleRows) {
    if (!Array.isArray(rows) || rows.length < 1 || rows.length > 2 ||
        !Array.isArray(rows[0]) || rows[0].length < 1 || rows[0].length > 2 ||
        rows.some(row => !Array.isArray(row) || row.length !== rows[0].length ||
            row.some(value => typeof value !== "string")) ||
        !Number.isInteger(visibleRows) || visibleRows < 0 || visibleRows > rows.length) {
        throw new Error("Organizador de áreas inválido");
    }
    container.replaceChildren();
    container.setAttribute("aria-hidden", "true");
    const grid = document.createElement("div");
    Object.assign(grid.style, {
        display:"grid",gridTemplateColumns:"repeat("+rows[0].length+",minmax(0,1fr))",
        maxWidth:"360px",margin:"14px 0",border:"2px solid #174c87",gap:"2px",
        background:"#174c87"
    });
    rows.forEach((row,r) => row.forEach((value,c) => {
        const cell=document.createElement("span");
        cell.dataset.areaCell="true";
        cell.dataset.revealed=String(r<visibleRows);
        cell.textContent=r<visibleRows?value:"";
        Object.assign(cell.style,{
            display:"grid",placeItems:"center",minHeight:"68px",padding:"8px",
            overflowWrap:"anywhere",color:"#18304c",
            background:r>=visibleRows?"#edf1f6":(r+c)%2?"#fbe8bd":"#dcebf9"
        });
        grid.append(cell);
    }));
    container.append(grid);
}
