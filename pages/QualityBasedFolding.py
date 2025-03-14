import streamlit as st
import random
import numpy as np

def generate_table_snippet():
    # Create random data: 10 rows x 10 columns.
    nrows, ncols = 10, 10
    data = np.random.randint(1, 100, (nrows, ncols))
    h_row = random.randint(0, nrows - 1)
    h_col = random.randint(0, ncols - 1)
    row_start = max(0, h_row - 2)
    row_end = min(nrows, h_row + 3)
    col_start = max(0, h_col - 2)
    col_end = min(ncols, h_col + 3)
    
    table_html = "<table style='border-collapse: collapse; width:100%;'>"
    table_html += "<tr>"
    table_html += "<th style='background-color: #f0f0f0; border: 1px solid #ccc; padding: 4px;'></th>"
    for c in range(col_start, col_end):
        table_html += f"<th style='background-color: #f0f0f0; border: 1px solid #ccc; padding: 4px;'>{c}</th>"
    table_html += "</tr>"
    
    for r in range(row_start, row_end):
        table_html += "<tr>"
        table_html += f"<th style='background-color: #f0f0f0; border: 1px solid #ccc; padding: 4px;'>{r}</th>"
        for c in range(col_start, col_end):
            if r == h_row and c == h_col:
                cell_style = "background-color: #FF8C00; color: white; border: 1px solid #ccc; padding: 4px;"
            elif r == h_row or c == h_col:
                cell_style = "background-color: #FFDAB9; border: 1px solid #ccc; padding: 4px;"
            else:
                cell_style = "border: 1px solid #ccc; padding: 4px;"
            table_html += f"<td style='{cell_style}'>{data[r, c]}</td>"
        table_html += "</tr>"
    table_html += "</table>"
    return table_html

def get_card_html(card):
    return f"""
    <div class="tinder--card">
      <div class="table-container" style="width: 100%; height: 70%; display: flex; align-items: center; justify-content: center;">
          {card['table_snippet']}
      </div>
      <div class="name-container" style="width: 100%; height: 30%; display: flex; align-items: center; justify-content: center;">
         <h3 style="margin: 0; font-size: 24px;">{card['name']}</h3>
      </div>
    </div>
    """

# Retrieve the labeling budget from session state (default to 10 if not set)
budget = st.session_state.get("labeling_budget", 10)

# Generate cards based on the labeling budget
cards = [
    {"name": f"Card {i+1}", "table_snippet": generate_table_snippet()}
    for i in range(budget)
]

# Define HTML template as a normal string and escape literal braces.
html_code = """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <script src="https://cdn.jsdelivr.net/npm/hammerjs@2.0.8/hammer.min.js"></script>
    <style>
      html, body {{ margin: 0; padding: 0; width: 100vw; height: 100vh; overflow: hidden; }}
      #tinder {{ width: 100vw; height: 100vh; display: flex; flex-direction: column; justify-content: flex-start; align-items: center; }}
      #progress-container {{ width: 90%; margin: 10px auto; text-align: center; }}
      #progress-bar {{ width: 100%; height: 20px; }}
      #progress-text {{
          background-color: white;
          display: inline-block;
          padding: 4px 8px;
          border-radius: 4px;
          margin-top: 4px;
      }}
      #tinder--cards {{ position: relative; width: 100%; height: 50%; display: flex; justify-content: center; align-items: center; }}
      .tinder--card {{ position: absolute; background: #fff; width: 90%; height: 100%; border-radius: 10px; box-shadow: 0 8px 30px rgba(0,0,0,0.2); overflow: hidden; transition: 0.3s; touch-action: none; }}
      #tinder--buttons {{ width: 100%; height: 15%; display: flex; justify-content: center; align-items: center; gap: 20px; margin-top: 10px; }}
      #tinder--buttons button {{ width: 80px; height: 80px; border-radius: 50%; background-color: #fff; border: 3px solid #e6e6e6; cursor: pointer; outline: none; font-size: 32px; transition: 0.2s; }}
      #tinder--buttons button:hover {{ transform: scale(1.1); }}
    </style>
  </head>
  <body>
    <div id="tinder">
      <!-- Progress bar container -->
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

# Combine the generated cards HTML with the template.
cards_html_concat = "".join([get_card_html(card) for card in cards])
final_html = html_code.format(cards_html=cards_html_concat, budget=budget)

st.title("Matelda - Swiping")
st.components.v1.html(final_html, height=800, scrolling=False)
