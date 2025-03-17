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

def generate_table_snippet():
    """
    Generate a 5×5 snippet from a random 10×10 table.
    Randomly choose a highlighted cell.
    Returns:
      - snippet: a list of dictionaries (each row) holding cell values.
      - h_row, h_col: the indices of the highlighted cell.
      - row_start, row_end, col_start, col_end: boundaries of the snippet.
    """
    nrows, ncols = 10, 10
    data = np.random.randint(1, 100, (nrows, ncols))
    h_row = random.randint(0, nrows - 1)
    h_col = random.randint(0, ncols - 1)
    row_start = max(0, h_row - 2)
    row_end = min(nrows, h_row + 3)
    col_start = max(0, h_col - 2)
    col_end = min(ncols, h_col + 3)
    
    snippet = []
    for r in range(row_start, row_end):
        row_obj = {"row": r}
        for c in range(col_start, col_end):
            row_obj[f"col{c}"] = int(data[r, c])
        snippet.append(row_obj)
    return snippet, h_row, h_col, row_start, row_end, col_start, col_end

def get_card_html(card):
    """
    Build HTML for a card:
      - Generate a snippet (5×5) and choose a highlighted cell.
      - Embed the snippet JSON.
      - Render a placeholder <div> for Tabulator.
      - Include a <script> block that initializes a Tabulator table with custom formatters.
    """
    snippet, h_row, h_col, row_start, row_end, col_start, col_end = generate_table_snippet()
    snippet_json = json.dumps(snippet)
    
    # Build Tabulator column definitions.
    # The first column shows the row number.
    columns = []
    columns.append('{title:"Row", field:"row", width:60}')
    for i in range(col_start, col_end):
        # For each cell, check:
        # - If the cell is the highlighted cell (i == h_col and row equals h_row) → darker orange.
        # - If the cell is in the highlighted row or column → lighter orange.
        formatter = (
            "function(cell, formatterParams, onRendered) { "
            "var rowData = cell.getRow().getData(); "
            "if(rowData.row == %d && cell.getColumn().getField() == 'col%d') { "
            "return \"<div style='background-color: #FF8C00; color: white; padding: 4px;'>\" + cell.getValue() + \"</div>\"; } "
            "else if(rowData.row == %d || cell.getColumn().getField() == 'col%d') { "
            "return \"<div style='background-color: #FFDAB9; padding: 4px;'>\" + cell.getValue() + \"</div>\"; } "
            "else { return cell.getValue(); } }" 
            % (h_row, h_col, h_row, h_col)
        )
        columns.append('{title:"Col %d", field:"col%d", formatter:%s}' % (i, i, formatter))
    columns_js = ", ".join(columns)
    
    card_id = card["id"]
    
    return f"""
    <div class="tinder--card" id="card-{card_id}" 
         style="position: absolute; width: 90%; height: 100%; border-radius: 10px; 
                box-shadow: 0 8px 30px rgba(0,0,0,0.2); overflow: hidden; 
                transition: 0.3s; touch-action: none; margin: 10px;">
      <div class="table-container" style="width: 100%; height: 70%; display: flex; align-items: center; justify-content: center;">
          <div id="table-{card_id}"></div>
      </div>
      <div class="name-container" style="width: 100%; height: 30%; display: flex; align-items: center; justify-content: center;">
         <h3 style="margin: 0; font-size: 24px;">{card['name']}</h3>
      </div>
      <script>
        // Data for this snippet.
        var tableData = {snippet_json};
        // Initialize Tabulator on the target element with custom formatters.
        new Tabulator("#table-{card_id}", {{
            data: tableData,
            layout:"fitColumns",
            columns: [{columns_js}],
        }});
      </script>
    </div>
    """

# Initialize session state for tracking if Quality Based Folding is running.
if "run_quality_folding" not in st.session_state:
    st.session_state.run_quality_folding = False

st.title("Quality Based Folding")

if not st.session_state.run_quality_folding:
    if st.button("Run Quality Based Folding"):
        with st.spinner("🔄 Processing... Please wait..."):
            time.sleep(3)
        st.session_state.run_quality_folding = True
        st.experimental_rerun()

if st.session_state.run_quality_folding:
    # Retrieve the labeling budget from session state (default to 10 if not set)
    budget = st.session_state.get("labeling_budget", 10)
    # Generate cards with interactive table snippets.
    cards = [
        {"id": i, "name": f"Card {i+1}"}
        for i in range(budget)
    ]
    
    # Build HTML for all cards.
    cards_html = "".join([get_card_html(card) for card in cards])
    
    # HTML template that includes Tabulator (via CDN) and our swipe layout.
    html_code = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
        <script src="https://cdn.jsdelivr.net/npm/hammerjs@2.0.8/hammer.min.js"></script>
        <!-- Include Tabulator CSS & JS -->
        <link href="https://unpkg.com/tabulator-tables@5.4.4/dist/css/tabulator.min.css" rel="stylesheet">
        <script type="text/javascript" src="https://unpkg.com/tabulator-tables@5.4.4/dist/js/tabulator.min.js"></script>
        <style>
          html, body {{
            margin: 0; padding: 0; width: 100vw; height: 100vh; overflow: hidden;
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
            position: relative; width: 100%; height: 50%; 
            display: flex; justify-content: center; align-items: center;
          }}
          .tinder--card {{
            position: absolute; background: #fff; width: 90%; height: 100%;
            border-radius: 10px; box-shadow: 0 8px 30px rgba(0,0,0,0.2); overflow: hidden;
            transition: 0.3s; touch-action: none; margin: 10px;
          }}
          #tinder--buttons {{
            width: 100%; height: 15%; display: flex; justify-content: center;
            align-items: center; gap: 20px; margin-top: 10px;
          }}
          #tinder--buttons button {{
            width: 80px; height: 80px; border-radius: 50%; background-color: #fff;
            border: 3px solid #e6e6e6; cursor: pointer; outline: none; font-size: 32px;
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
          var initialCards = document.querySelectorAll('.tinder--card');
          initialCards.forEach(function(card) {{
            attachHammer(card);
          }});
          updateCards();
        </script>
      </body>
    </html>
    """
    
    st.write("Swipe the correct cells to the right and the incorrect to the left.")
    st.components.v1.html(html_code, height=800, scrolling=False)
