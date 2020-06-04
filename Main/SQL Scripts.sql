-- SQL Scripts to work off of 

-- See which teams win the tip off most frequently, per season

SELECT season, Possession, COUNT(*)
FROM (
	SELECT season
	, Possession
	, Rank() OVER (PARTITION BY game_url ORDER BY "index") as PossessionVal
	FROM season_data
) p
WHERE PossessionVal = 1
and season = 2020
GROUP BY season, Possession
order by 1,3 desc;


-- Probability of scoring first, given they won the tip

CREATE VIEW vw_possession_ranking
AS

	SELECT "index"
	, season
	, game_url
	, Possession
	, CASE WHEN winning_tip = 'away_center' then visiting_center else home_center end as WinningTipOffPlayer
	, CASE WHEN winning_tip = 'away_center' then home_center else visiting_center end as LosingTipOffPlayer
	, Rank() OVER (PARTITION BY game_url ORDER BY "index") as PossessionVal
	FROM season_data;


-- Query 1 to show the winning tip team and the team who scored first and see if they line up
WITH p_val_table as 
(
	SELECT season, game_url, Possession, PossessionVal
	FROM vw_possession_ranking
)
SELECT p.season, p.game_url
, t.Possession as WinningTipTeam
, s.Possession as FirstScoringTeam
, CASE WHEN t.Possession = s.Possession THEN 1 ELSE 0 END as WinningTipTeamScoredFirst
FROM (
	SELECT season, game_url
	, MIN(PossessionVal) as WinningTipPossession
	, MAX(PossessionVal) as ScoringPossession
	FROM vw_possession_ranking
	GROUP BY season, game_url
) p
JOIN p_val_table t on t.season = p.season 
	AND t.game_url = p.game_url 
	AND p.WinningTipPossession = t.PossessionVal
JOIN p_val_table s on s.season = p.season 
	AND s.game_url = p.game_url 
	AND p.ScoringPossession = s.PossessionVal
limit 10;


-- Query 2 that actually does calculations by year
WITH p_val_table as 
(
	SELECT season, game_url, Possession, PossessionVal
	FROM vw_possession_ranking
)
SELECT p.season, AVG(CASE WHEN t.Possession = s.Possession THEN 1 ELSE 0 END) as WinningTipTeamScoredFirst
FROM (
	SELECT season, game_url
	, MIN(PossessionVal) as WinningTipPossession
	, MAX(PossessionVal) as ScoringPossession
	FROM vw_possession_ranking
	GROUP BY season, game_url
) p
JOIN p_val_table t on t.season = p.season 
	AND t.game_url = p.game_url 
	AND p.WinningTipPossession = t.PossessionVal
JOIN p_val_table s on s.season = p.season 
	AND s.game_url = p.game_url 
	AND p.ScoringPossession = s.PossessionVal
GROUP BY p.season
order by p.season;

-- Query 3 that actually does calculations by year and team
WITH p_val_table as 
(
	SELECT season, game_url, Possession, PossessionVal
	FROM vw_possession_ranking
)
SELECT p.season, t.Possession, AVG(CASE WHEN t.Possession = s.Possession THEN 1 ELSE 0 END) as WinningTipTeamScoredFirst
FROM (
	SELECT season, game_url
	, MIN(PossessionVal) as WinningTipPossession
	, MAX(PossessionVal) as ScoringPossession
	FROM vw_possession_ranking
	GROUP BY season, game_url
) p
JOIN p_val_table t on t.season = p.season 
	AND t.game_url = p.game_url 
	AND p.WinningTipPossession = t.PossessionVal
JOIN p_val_table s on s.season = p.season 
	AND s.game_url = p.game_url 
	AND p.ScoringPossession = s.PossessionVal
GROUP BY p.season, t.Possession
order by 1,3 desc;



-- Players career  tipoff win and losses
SELECT p.PlayerId
, p.Name
, p.Height
, p.Birthday
, IfNULL(w.Wins, 0) AS TipOffWins
, IfNULL(l.Losses, 0) AS TipOfflosses
, case when w.Wins is null and l.losses is null then 0
	else IfNULL(w.Wins, 0) * 1.0 / (IfNULL(w.Wins, 0) + IfNULL(l.Losses, 0)) end as WinningPct
FROM players p
left join (
	select p.PlayerID, count(distinct game_url) as Wins
	from players p
	join vw_possession_ranking w on w.WinningTipOffPlayer = p.PlayerID
	GROUP BY p.PlayerID
) w on p.PlayerID = w.PlayerID
left join
(
	select p.PlayerID, count(distinct game_url) as Losses
	from players p
	join vw_possession_ranking l on l.LosingTipOffPlayer = p.playerID
	GROUP BY p.PlayerID
	order by 2 desc
) l on p.PlayerID = l.PlayerId
WHERE IFNULL(w.Wins, 0) > 10
order by WinningPct desc
limit 20;
