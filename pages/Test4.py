import streamlit as st
import random
import numpy as np
import time
import json

# Hide default Streamlit menu
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.page_link("app.py", label="Matelda")
    st.page_link("pages/Configurations.py", label="Configurations")
    st.page_link("pages/DomainBasedFolding.py", label="Domain Based Folding")
    st.page_link("pages/QualityBasedFolding.py", label="Quality Based Folding")
    st.page_link("pages/Labeling.py", label="Labeling")
    st.page_link("pages/ErrorDetection.py", label="Error Detection")
    st.page_link("pages/Results.py", label="Results")

def generate_table_data():
    """
    Generate a 10×10 table of random integers, plus a randomly chosen 'highlighted' cell.
    Returns:
      data_list  - the table data as a list of dicts (for Tabulator).
      h_row      - highlighted row index
      h_col      - highlighted column index
    """
    nrows, ncols = 10, 10
    arr = np.random.randint(1, 100, (nrows, ncols))
    # Pick random highlighted cell
    h_row = random.randint(0, nrows - 1)
    h_col = random.randint(0, ncols - 1)
    
    # Convert to list-of-dicts for Tabulator
    data_list = []
    for r in range(nrows):
        row_dict = {"rowIndex": r}  # We'll store the row index in a field
        for c in range(ncols):
            row_dict[f"col{c}"] = int(arr[r, c])
        data_list.append(row_dict)
    return data_list, h_row, h_col

def get_card_html(card):
    """
    Build HTML for one "card":
      - Creates a Tabulator table of 10×10 random data
      - Highlights a random cell in darker orange
      - Highlights that cell's row/column in lighter orange
      - Avoids f-string curly-brace conflicts by using normal strings + .replace()
    """
    data_list, h_row, h_col = generate_table_data()
    table_data_json = json.dumps(data_list)
    
    # 1) A normal (non-f) triple-quoted string for our cell formatter JavaScript
    #    We temporarily use placeholders H_ROW and H_COL, then do .replace() to insert real values.
    cell_formatter_js = """
function(cell, formatterParams, onRendered) {
    let rowVal = cell.getRow().getData().rowIndex;
    let colField = cell.getColumn().getField();
    let val = cell.getValue();

    // If this cell is exactly the highlighted cell
    if(rowVal == H_ROW && colField == "colH_COL") {
      return "<div style='background-color: #FF8C00; color:white; padding:4px;'>" + val + "</div>";
    }
    // If this cell is in the same row or column as the highlight
    else if(rowVal == H_ROW || colField == "colH_COL") {
      return "<div style='background-color: #FFDAB9; padding:4px;'>" + val + "</div>";
    }
    // Otherwise normal cell
    else {
      return val;
    }
}
"""
    # Insert the real highlight row/col into that code
    cell_formatter_js = cell_formatter_js.replace("H_ROW", str(h_row))
    cell_formatter_js = cell_formatter_js.replace("H_COL", str(h_col))

    # 2) A normal string for the rowIndex formatter
    row_index_formatter_js = """
function(cell, formatterParams, onRendered) {
    let rowVal = cell.getValue();
    if(rowVal == H_ROW) {
      return "<div style='background-color: #FFDAB9; padding:4px;'>" + rowVal + "</div>";
    } else {
      return rowVal;
    }
}
"""
    row_index_formatter_js = row_index_formatter_js.replace("H_ROW", str(h_row))

    # 3) Build the columns array in JavaScript syntax
    #    We'll do so by string concatenation (avoiding extra braces in f-strings).
    columns_js_parts = []

    # First column: rowIndex
    col_def_row_index = (
        "{"
        '"title":"Row",'
        '"field":"rowIndex",'
        '"width":60,'
        f'"formatter":{row_index_formatter_js}'
        "}"
    )
    columns_js_parts.append(col_def_row_index)

    # Next columns: col0..col9
    for c in range(10):
        col_def = (
            "{"
            f'"title":"Col {c}",'
            f'"field":"col{c}",'
            f'"formatter":{cell_formatter_js}'
            "}"
        )
        columns_js_parts.append(col_def)

    # Join them into a single JS array: [ {...}, {...}, ... ]
    columns_js_str = "[" + ",".join(columns_js_parts) + "]"

    # 4) Final card HTML
    card_id = card["id"]
    return f"""
    <div class="tinder--card" id="card-{card_id}"
         style="position: absolute; width: 90%; height: 100%; border-radius: 10px; 
                box-shadow: 0 8px 30px rgba(0,0,0,0.2); overflow: hidden; 
                transition: 0.3s; touch-action: none; margin: 10px;">
      <div class="table-container" style="width: 100%; height: 70%; display: flex; align-items: center; justify-content: center;">
          <div id="table-{card_id}" style="width:95%; height:95%;"></div>
      </div>
      <div class="name-container" style="width: 100%; height: 30%; display: flex; align-items: center; justify-content: center;">
         <h3 style="margin: 0; font-size: 24px;">{card['name']}</h3>
      </div>
      <script>
        // Build a Tabulator for this card
        new Tabulator("#table-{card_id}", {{
          data:{table_data_json},    // the 10×10 data
          layout:"fitColumns",
          pagination:"local",        // enable local pagination for demonstration
          paginationSize:5,
          paginationSizeSelector:[5,10],
          columns:{columns_js_str},
        }});
      </script>
    </div>
    """

# ----------------------------------------------------------------------------
# Streamlit App
# ----------------------------------------------------------------------------

if "run_quality_folding" not in st.session_state:
    st.session_state.run_quality_folding = False

st.title("Quality Based Folding")

if not st.session_state.run_quality_folding:
    if st.button("Run Quality Based Folding"):
        with st.spinner("🔄 Processing... Please wait..."):
            time.sleep(3)
        st.session_state.run_quality_folding = True
        st.rerun()

if st.session_state.run_quality_folding:
    budget = st.session_state.get("labeling_budget", 10)
    cards = [{"id": i, "name": f"Card {i+1}"} for i in range(budget)]
    
    cards_html = "".join([get_card_html(card) for card in cards])

    html_template = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
        <script src="https://cdn.jsdelivr.net/npm/hammerjs@2.0.8/hammer.min.js"></script>
        <!-- Tabulator CSS & JS -->
        <link href="https://unpkg.com/tabulator-tables@5.4.4/dist/css/tabulator.min.css" rel="stylesheet">
        <script type="text/javascript" src="https://unpkg.com/tabulator-tables@5.4.4/dist/js/tabulator.min.js"></script>
        <style>
          html, body {{
            margin: 0; padding: 0; width: 100vw; height: 100vh; overflow: hidden;
            background-color: #111;
          }}
          #tinder {{
            width: 100vw; height: 100vh; display: flex; flex-direction: column;
            justify-content: flex-start; align-items: center;
          }}
          #progress-container {{
            width: 90%; margin: 10px auto; text-align: center;
          }}
          #progress-bar {{
            width: 100%; height: 20px;
          }}
          #progress-text {{
            background-color: white; display: inline-block; padding: 4px 8px;
            border-radius: 4px; margin-top: 4px;
          }}
          #tinder--cards {{
            position: relative; width: 100%; height: 60%;
            display: flex; justify-content: center; align-items: center;
          }}
          .tinder--card {{
            position: absolute; background: #333; width: 90%; height: 100%;
            border-radius: 10px; box-shadow: 0 8px 30px rgba(0,0,0,0.5);
            overflow: hidden; transition: 0.3s; touch-action: none; margin: 10px;
          }}
          #tinder--buttons {{
            width: 100%; height: 15%; display: flex; justify-content: center;
            align-items: center; gap: 20px; margin-top: 10px;
          }}
          #tinder--buttons button {{
            width: 80px; height: 80px; border-radius: 50%;
            background-color: #444; color: #fff; border: 2px solid #888;
            cursor: pointer; outline: none; font-size: 32px;
            transition: 0.2s;
          }}
          #tinder--buttons button:hover {{
            transform: scale(1.1);
          }}
        </style>
      </head>
      <body>
        <div id="tinder">
          <div id="progress-container">
            <progress id="progress-bar" value="0" max="{budget}"></progress>
            <div id="progress-text">0% (0/{budget})</div>
          </div>
          <div id="tinder--cards">
            {cards_html}
          </div>
          <div id="tinder--buttons">
            <button id="dislike">👎</button>
            <button id="back">↩️</button>
            <button id="like">👍</button>
          </div>
        </div>
        <script>
          var removedCards = [];
          var total = {budget};

          function updateCards() {{
            var allCards = document.querySelectorAll('.tinder--card');
            var remaining = allCards.length;
            var completed = total - remaining;
            updateProgressBar(completed);
            allCards.forEach(function(card, index) {{
              card.style.zIndex = remaining - index;
              card.style.transform = 'translate(0, 0) rotate(0)';
              card.style.opacity = 1;
            }});
          }}

          function updateProgressBar(completed) {{
            var progressBar = document.getElementById('progress-bar');
            var progressText = document.getElementById('progress-text');
            progressBar.value = completed;
            var percent = Math.round((completed / total) * 100);
            progressText.innerHTML = percent + "% (" + completed + "/" + total + ")";
          }}

          function getTopCard() {{
            return document.querySelector('.tinder--card');
          }}

          function removeCard(like) {{
            var card = getTopCard();
            if (!card) return;
            var toX = like ? 100 : -100;
            var angle = like ? 15 : -15;
            card.style.transform = 'translate(' + toX + 'vw, -10vh) rotate(' + angle + 'deg)';
            card.style.opacity = 0;
            removedCards.push(card);
            setTimeout(function() {{
              card.remove();
              updateCards();
            }}, 300);
          }}

          document.getElementById('dislike').addEventListener('click', function() {{
            removeCard(false);
          }});
          document.getElementById('like').addEventListener('click', function() {{
            removeCard(true);
          }});
          document.getElementById('back').addEventListener('click', function() {{
            if (removedCards.length > 0) {{
              var card = removedCards.pop();
              var cardsContainer = document.getElementById('tinder--cards');
              cardsContainer.insertBefore(card, cardsContainer.firstChild);
              card.style.transform = 'translate(0, 0) rotate(0)';
              card.style.opacity = 1;
              attachHammer(card);
              updateCards();
            }}
          }});

          function attachHammer(card) {{
            var hammertime = new Hammer(card);
            hammertime.on('pan', function(event) {{
              card.classList.add('moving');
              if (event.deltaX === 0) return;
              if (event.center.x === 0 && event.center.y === 0) return;
              var xMulti = event.deltaX * 0.03;
              var yMulti = event.deltaY / 80;
              var rotate = xMulti * yMulti;
              card.style.transform = 'translate(' + event.deltaX + 'px, ' + event.deltaY + 'px) rotate(' + rotate + 'deg)';
            }});
            hammertime.on('panend', function(event) {{
              card.classList.remove('moving');
              var moveOutWidth = document.body.clientWidth;
              var keep = Math.abs(event.deltaX) < 80 && Math.abs(event.velocityX) < 0.5;
              if (keep) {{
                card.style.transform = '';
              }} else {{
                var endX = Math.max(Math.abs(event.velocityX) * moveOutWidth, moveOutWidth);
                var toX = event.deltaX > 0 ? endX : -endX;
                var endY = Math.abs(event.velocityY) * moveOutWidth;
                var toY = event.deltaY > 0 ? endY : -endY;
                var xMulti = event.deltaX * 0.03;
                var yMulti = event.deltaY / 80;
                var rotate = xMulti * yMulti;
                card.style.transform = 'translate(' + toX + 'px, ' + (toY + event.deltaY) + 'px) rotate(' + rotate + 'deg)';
                card.style.opacity = 0;
                removedCards.push(card);
                setTimeout(function() {{
                  card.remove();
                  updateCards();
                }}, 300);
              }}
            }});
          }}

          // Attach Hammer to initial cards
          var initialCards = document.querySelectorAll('.tinder--card');
          initialCards.forEach(function(card) {{
            attachHammer(card);
          }});
          updateCards();
        </script>
      </body>
    </html>
    """

    st.write("Swipe left/right or use the buttons to label. Each card uses Tabulator with pagination, and highlights a random cell.")
    st.components.v1.html(html_template, height=800, scrolling=False)
