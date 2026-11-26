"""
International football analysis: answers all five questions.

Put results.csv, shootouts.csv and goalscorers.csv in the same folder and run:
    python football_analysis.py
Works whether or not the files have a header row.
"""
import pandas as pd

RES_COLS = ['date', 'home_team', 'away_team', 'home_score', 'away_score',
            'tournament', 'city', 'country', 'neutral']
SHO_COLS = ['date', 'home_team', 'away_team', 'winner', 'first_shooter']
GS_COLS = ['date', 'home_team', 'away_team', 'team', 'scorer', 'minute',
           'own_goal', 'penalty']


def load(path, cols):
    """Load a CSV with or without a header row."""
    with open(path, encoding='utf-8') as f:
        has_header = f.readline().strip().lower().startswith('date')
    if has_header:
        df = pd.read_csv(path)
    else:
        df = pd.read_csv(path, names=cols)
    df['date'] = pd.to_datetime(df['date'])
    return df

##load csv files
results = load('results.csv', RES_COLS)
shootouts = load('shootouts.csv', SHO_COLS)
goalscorers = load('goalscorers.csv', GS_COLS)

for col in ('own_goal', 'penalty'):
    goalscorers[col] = goalscorers[col].astype(str).str.upper().eq('TRUE')

# Reliable join key: date + home_team + away_team
for df in (results, shootouts, goalscorers):
    df['match_id'] = (df['date'].dt.strftime('%Y-%m-%d') + '|' +
                      df['home_team'] + '|' + df['away_team'])

print("=== #3 Join key: date|home_team|away_team ===")
print("Duplicate keys in results:        ", results['match_id'].duplicated().sum())
print("Duplicate keys in shootouts:      ", shootouts['match_id'].duplicated().sum())
print("Shootouts with no matching result:",
      (~shootouts['match_id'].isin(results['match_id'])).sum())
print("Goal rows with no matching result:",
      (~goalscorers['match_id'].isin(results['match_id'])).sum())

#1--Create a query that calculates the average number of goals per game between 1900 and 2000.
in_range = results['date'].dt.year.between(1900, 2000)
avg_goals = (results.loc[in_range, 'home_score'] +
             results.loc[in_range, 'away_score']).mean()
print("\n=== #1 Average goals per game, 1900-2000 ===")
print(f"{avg_goals:.3f} goals per game over {in_range.sum()} matches")

 #2 Shootout wins by country, alphabetical

wins = shootouts.groupby('winner').size().rename('wins').sort_index()
print("\n=== #2 Shootout wins by country (A-Z) ===")
print(wins.to_string())

# #4 Teams that won a shootout after a 1-1 draw

merged = results.merge(shootouts[['match_id', 'winner']], on='match_id')
one_one = merged[(merged['home_score'] == 1) & (merged['away_score'] == 1)]
after_11 = one_one.groupby('winner').size().rename('wins').sort_values(ascending=False)
print("\n=== #4 Shootout wins after a 1-1 draw ===")
print(after_11.to_string())

# #5 Top goalscorer per tournament and share of all tournament goals

gs = goalscorers.merge(results[['match_id', 'tournament']],
                       on='match_id', how='left')
gs = gs[~gs['own_goal']]

scorer_goals = (gs.groupby(['tournament', 'scorer']).size()
                  .rename('goals').reset_index())

tournament_goals = (results
                    .assign(total=results['home_score'] + results['away_score'])
                    .groupby('tournament')['total'].sum()
                    .rename('tournament_goals').reset_index())

top = scorer_goals[scorer_goals['goals'] ==
                   scorer_goals.groupby('tournament')['goals'].transform('max')]
top = top.merge(tournament_goals, on='tournament')
top['pct_of_tournament_goals'] = (100 * top['goals'] /
                                  top['tournament_goals']).round(2)

print("\n=== #5 Top scorer per tournament ===")
print(top.sort_values('tournament').to_string(index=False))