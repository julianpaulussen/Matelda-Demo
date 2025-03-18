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
      data_list  - the table data as a list of dicts (for Tabulator)
      h_row      - highlighted row index
      h_col      - highlighted column index
    """
    nrows, ncols = 10, 10
    arr = np.random.randint(1, 100, (nrows, ncols))
    h_row = random.randint(0, nrows - 1)
    h_col = random.randint(0, ncols - 1)
    data_list = []
    for r in range(nrows):
        row_dict = {"rowIndex": r}
        for c in range(ncols):
            row_dict[f"col{c}"] = int(arr[r, c])
        data_list.append(row_dict)
    return data_list, h_row, h_col

def get_card_html(card):
    """
    Build HTML for one card with:
      - A 10×10 table with one highlighted cell.
      - A top row with the card name and the Inspect Table toggle (info button removed).
      - A left-aligned section with a header "Error Detection Strategies:" and 8 pill elements labeled "Strategy01" to "Strategy08".
    """
    data_list, h_row, h_col = generate_table_data()
    table_data_json = json.dumps(data_list)
    
    # Formatter functions for table cells
    cell_formatter_js = f"""
var cellFormatter = function(cell, formatterParams, onRendered) {{
    var rowVal = cell.getRow().getData().rowIndex;
    var colField = cell.getColumn().getField();
    var val = cell.getValue();
    if(rowVal == {h_row} && colField == "col{h_col}") {{
       return "<div style='background-color: #FF8C00; color:white; padding:4px;'>" + val + "</div>";
    }} else if(rowVal == {h_row} || colField == "col{h_col}") {{
       return "<div style='background-color: #FFDAB9; padding:4px;'>" + val + "</div>";
    }} else {{
       return val;
    }}
}};
"""
    row_index_formatter_js = f"""
var rowIndexFormatter = function(cell, formatterParams, onRendered) {{
    var rowVal = cell.getValue();
    if(rowVal == {h_row}) {{
       return "<div style='background-color: #FFDAB9; padding:4px;'>" + rowVal + "</div>";
    }} else {{
       return rowVal;
    }}
}};
"""
    card_id = card["id"]

    # Create eight pill elements with labels "Strategy01" to "Strategy08"
    pills_html = "".join([
        f'<span class="pill" id="pill-{i}-{card_id}" style="padding: 4px 8px; font-size:9px; border-radius: 16px; background: #ddd;">Strategy{(i+1):02d}</span>'
        for i in range(8)
    ])
    
    return f"""
    <div class="tinder--card" id="card-{card_id}" style="position: absolute; width: 90%; height: 100%; border-radius: 10px; background: #fff; overflow: hidden; transition: 0.3s; touch-action: none; margin: 10px;">
      <div class="flip-card" style="width: 100%; height: 100%; perspective: 1000px;">
        <div class="flip-card-inner" id="flip-card-inner-{card_id}" style="position: relative; width: 100%; height: 100%; transition: transform 0.8s ease; transform-style: preserve-3d;">
          <!-- Front of Card -->
          <div class="flip-card-front" style="position: absolute; width: 100%; height: 100%; backface-visibility: hidden;">
            <div class="table-container" id="table-container-{card_id}" style="width: 100%; height: 70%; display: flex; align-items: center; justify-content: center;">
                <div id="table-{card_id}" style="width:95%; height:95%;"></div>
            </div>
            <div class="info-row" style="display: flex; justify-content: space-between; align-items: center; padding: 4px 10px;">
               <div class="name-container">
                 <h3 style="margin: 0; font-size: 24px;">{card['name']}</h3>
               </div>
               <div class="controls-container" style="display: flex; align-items: center;">
                 <div class="inspect-container" style="display: flex; align-items: center;">
                   <label class="switch">
                     <input type="checkbox" id="inspect-{card_id}">
                     <span class="slider round"></span>
                   </label>
                   <span style="margin-left: 8px; font-size: 14px; color: #555;">Inspect Table</span>
                 </div>
               </div>
            </div>
            <!-- New header and pills container aligned to the left -->
            <div class="pills-header" style="padding: 4px 10px;">
              <h4 style="margin: 0; font-size: 16px;">Error Detection Strategies:</h4>
            </div>
            <div class="pills-container" style="display: flex; justify-content: flex-start; gap: 8px; padding: 4px 10px;">
                {pills_html}
            </div>
          </div>
          <!-- Back of Card (Empty) -->
          <div class="flip-card-back" id="flip-card-back-{card_id}" style="position: absolute; width: 100%; height: 100%; backface-visibility: hidden; background: white; transform: rotateY(180deg);">
            <!-- Empty backside -->
          </div>
        </div>
      </div>
      <script>
        {cell_formatter_js}
        {row_index_formatter_js}
        // Save full table data and column definitions for full mode
        var fullData_{card_id} = {table_data_json};
        var fullColumns_{card_id} = [];
        fullColumns_{card_id}.push({{title:"Row", field:"rowIndex", width:60, formatter: rowIndexFormatter}});
        for (var i = 0; i < 10; i++) {{
            fullColumns_{card_id}.push({{title: "Col " + i, field:"col" + i, formatter: cellFormatter}});
        }}
        
        // Variables to store the zoom (excerpt) view data and columns
        var zoomData_{card_id} = null;
        var zoomColumns_{card_id} = null;
        
        function getSubsetData(data, startRow, endRow, startCol, endCol) {{
            var subset = [];
            for (var i = startRow; i < endRow; i++) {{
                var row = data[i];
                var newRow = {{ "rowIndex": row.rowIndex }};
                for (var j = startCol; j < endCol; j++) {{
                    newRow["col" + j] = row["col" + j];
                }}
                subset.push(newRow);
            }}
            return subset;
        }}
        
        function getSubsetColumns(startCol, endCol) {{
            var cols = [];
            cols.push({{title:"Row", field:"rowIndex", width:60, formatter: rowIndexFormatter}});
            for (var i = startCol; i < endCol; i++) {{
                cols.push({{title: "Col " + i, field:"col" + i, formatter: cellFormatter}});
            }}
            return cols;
        }}
        
        function buildTabulator_{card_id}(mode) {{
            var container = document.getElementById("table-{card_id}");
            container.innerHTML = "";
            if (mode === "full") {{
                new Tabulator(container, {{
                    data: fullData_{card_id},
                    layout:"fitColumns",
                    pagination:"local",
                    paginationSize:10,
                    paginationSizeSelector:[10,20],
                    columns: fullColumns_{card_id},
                }});
            }} else {{
                // Zoom mode: use stored zoomData if available, otherwise compute it once
                if (!zoomData_{card_id}) {{
                    var hRow = {h_row};
                    var hCol = {h_col};
                    var nrows = 10;
                    var ncols = 10;
                    var startRow = Math.max(0, hRow - 2);
                    var endRow = Math.min(nrows, hRow + 3);
                    var startCol = Math.max(0, hCol - 2);
                    var endCol = Math.min(ncols, hCol + 3);
                    zoomData_{card_id} = getSubsetData(fullData_{card_id}, startRow, endRow, startCol, endCol);
                    zoomColumns_{card_id} = getSubsetColumns(startCol, endCol);
                }}
                new Tabulator(container, {{
                    data: zoomData_{card_id},
                    layout:"fitColumns",
                    pagination:"local",
                    paginationSize:5,
                    paginationSizeSelector:[5,10],
                    columns: zoomColumns_{card_id},
                }});
            }}
        }}
        
        // Initialize in zoom mode (default) using the stored zoom excerpt
        buildTabulator_{card_id}("zoom");
        document.getElementById("table-container-{card_id}").style.pointerEvents = "none";
        
        // Toggle event listener for the Inspect Table switch
        var inspectCheckbox = document.getElementById("inspect-{card_id}");
        inspectCheckbox.addEventListener("change", function() {{
            if (this.checked) {{
                buildTabulator_{card_id}("full");
                document.getElementById("table-container-{card_id}").style.pointerEvents = "auto";
            }} else {{
                buildTabulator_{card_id}("zoom");
                document.getElementById("table-container-{card_id}").style.pointerEvents = "none";
            }}
        }});
        
        // Card flipping functionality (backside click flips back)
        var flipCardInner = document.getElementById("flip-card-inner-{card_id}");
        var flipCardBack = document.getElementById("flip-card-back-{card_id}");
        
        flipCardBack.addEventListener("click", function() {{
            flipCardInner.style.transform = "rotateY(0deg)";
        }});
        
        // Randomly highlight some pills in the pills container
        (function() {{
            var pills = document.querySelectorAll("#card-{card_id} .pill");
            pills.forEach(function(pill) {{
                if (Math.random() < 0.3) {{  // ~30% chance to highlight
                    pill.style.backgroundColor = "#FF8C00";
                    pill.style.color = "white";
                }}
            }});
        }})();
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

# Generate cards based on labeling budget and table_locations (with replacement if needed)
if st.session_state.run_quality_folding:
    budget = st.session_state.get("labeling_budget", 10)
    if "table_locations" in st.session_state:
        available = list(st.session_state.table_locations.items())
        cards = []
        for i in range(budget):
            table, domain_fold = random.choice(available)
            cards.append({"id": i, "name": f"{domain_fold} – {table}"})
    else:
        cards = [{"id": i, "name": f"Card {i+1}"} for i in range(5)]
    
    cards_html = "".join([get_card_html(card) for card in cards])
    
    # HTML template with updated styling and card flip animation
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
            margin: 0; 
            padding: 0; 
            width: 100vw; 
            height: 100vh; 
            overflow: hidden;
            background-color: #111;
          }}
          #tinder {{
            position: relative;
            width: 100vw; 
            height: 100vh; 
            display: flex; 
            flex-direction: column;
            justify-content: flex-start; 
            align-items: center;
          }}
          #progress-container {{
            width: 90%; 
            margin: 10px auto; 
            text-align: center;
          }}
          #progress-bar {{
            width: 100%; 
            height: 20px;
          }}
          #progress-text {{
            background-color: white; 
            display: inline-block; 
            padding: 4px 8px;
            border-radius: 4px; 
            margin-top: 4px;
          }}
          #tinder--cards {{
            position: relative; 
            width: 100%; 
            height: 60%;
            display: flex; 
            justify-content: center; 
            align-items: center;
          }}
          .tinder--card {{
            position: absolute; 
            background: #fff;
            width: 90%; 
            height: 100%;
            border-radius: 10px; 
            overflow: hidden; 
            transition: 0.3s; 
            touch-action: none; 
            margin: 10px;
          }}
          #tinder--buttons {{
            width: 100%; 
            height: 15%; 
            display: flex; 
            justify-content: center;
            align-items: center; 
            gap: 20px; 
            margin-top: 10px;
          }}
          #tinder--buttons button {{
            width: 80px; 
            height: 80px; 
            border-radius: 50%;
            background-color: #444; 
            color: #fff; 
            border: 2px solid #888;
            cursor: pointer; 
            outline: none; 
            font-size: 32px;
            transition: 0.2s;
          }}
          #tinder--buttons button:hover {{
            transform: scale(1.1);
          }}
          /* Modern toggle switch styles */
          .switch {{
            position: relative;
            display: inline-block;
            width: 50px;
            height: 24px;
          }}
          .switch input {{
            opacity: 0;
            width: 0;
            height: 0;
          }}
          .slider {{
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: .4s;
            border-radius: 24px;
          }}
          .slider:before {{
            position: absolute;
            content: "";
            height: 18px;
            width: 18px;
            left: 3px;
            bottom: 3px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
          }}
          input:checked + .slider {{
            background-color: #2196F3;
          }}
          input:checked + .slider:before {{
            transform: translateX(26px);
          }}
          /* Modern Tabulator styling */
          .tabulator {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 14px;
          }}
          .tabulator .tabulator-header {{
            background: #f4f4f4;
            color: #333;
            font-weight: bold;
            border: none;
          }}
          .tabulator .tabulator-cell {{
            border: 1px solid #e0e0e0;
            padding: 4px;
          }}
        </style>
      </head>
      <body>
        <div id="tinder">
          <div id="progress-container">
            <progress id="progress-bar" value="0" max="{len(cards)}"></progress>
            <div id="progress-text">0% (0/{len(cards)})</div>
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
          var total = {len(cards)};

          function updateCards() {{
            var allCards = document.querySelectorAll('.tinder--card');
            var remaining = allCards.length;
            var completed = total - remaining;
            updateProgressBar(completed);
            allCards.forEach(function(card, index) {{
              card.style.zIndex = 100 + (remaining - index);
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
    
    st.info("Swipe left/right or use the buttons to label the sampled cell. If you are done, continue with the Next-Button below the cards.")
    st.components.v1.html(html_template, height=800, scrolling=False)

    st.markdown("---")

    if st.button("Next"):
      st.switch_page("pages/ErrorDetection.py")
