/*This script takes 17 minutes to run.*/

/*Create index on main records table so that the rest of this script runs faster.*/
CREATE INDEX records_idx ON records(mode,map,brawler);
CREATE INDEX records_idx2 ON records(mode,map,brawler,player_id);

ANALYZE;

/*Drop previous aggregation tables.*/
DROP TABLE IF EXISTS population_aggs_high;
DROP TABLE IF EXISTS population_aggs_mid;
DROP TABLE IF EXISTS population_aggs_low;
DROP TABLE IF EXISTS individual_aggs_high;
DROP TABLE IF EXISTS individual_aggs_mid;
DROP TABLE IF EXISTS individual_aggs_low;

/*Create population aggregation tables.*/
SELECT mode, map, brawler,
	SUM(CASE WHEN mode IN ('soloShowdown', 'loneStar') AND showdown_rank <= 4 THEN 1
		WHEN mode IN ('soloShowdown', 'loneStar') AND showdown_rank > 4 THEN 0
		WHEN mode IN ('duoShowdown') AND showdown_rank <= 2 THEN 1
		WHEN mode IN ('duoShowdown') AND showdown_rank > 2 THEN 0 ELSE win END) AS wins, 
	COUNT(brawler) AS matches_played
INTO population_aggs_high
FROM records
WHERE trophies >= 550
GROUP BY map, mode, brawler;

SELECT mode, map, brawler,
	SUM(CASE WHEN mode IN ('soloShowdown', 'loneStar') AND showdown_rank <= 4 THEN 1
		WHEN mode IN ('soloShowdown', 'loneStar') AND showdown_rank > 4 THEN 0
		WHEN mode IN ('duoShowdown') AND showdown_rank <= 2 THEN 1
		WHEN mode IN ('duoShowdown') AND showdown_rank > 2 THEN 0 ELSE win END) AS wins, 
	COUNT(brawler) AS matches_played
INTO population_aggs_mid
FROM records
WHERE trophies >= 300
AND trophies < 550
GROUP BY map, mode, brawler;

SELECT mode, map, brawler,
	SUM(CASE WHEN mode IN ('soloShowdown', 'loneStar') AND showdown_rank <= 4 THEN 1
		WHEN mode IN ('soloShowdown', 'loneStar') AND showdown_rank > 4 THEN 0
		WHEN mode IN ('duoShowdown') AND showdown_rank <= 2 THEN 1
		WHEN mode IN ('duoShowdown') AND showdown_rank > 2 THEN 0 ELSE win END) AS wins, 
	COUNT(brawler) AS matches_played
INTO population_aggs_low
FROM records
WHERE trophies < 300
GROUP BY map, mode, brawler;

/*Create individual aggregation tables.*/
SELECT mode, map, brawler, player_id,
	SUM(CASE WHEN mode IN ('soloShowdown', 'loneStar') AND showdown_rank <= 4 THEN 1
		WHEN mode IN ('soloShowdown', 'loneStar') AND showdown_rank > 4 THEN 0
		WHEN mode IN ('duoShowdown') AND showdown_rank <= 2 THEN 1
		WHEN mode IN ('duoShowdown') AND showdown_rank > 2 THEN 0 ELSE win END) AS wins, 
	COUNT(brawler) AS matches_played
INTO individual_aggs_high
FROM records
WHERE trophies >= 550
GROUP BY map, mode, brawler, player_id;

SELECT mode, map, brawler, player_id,
	SUM(CASE WHEN mode IN ('soloShowdown', 'loneStar') AND showdown_rank <= 4 THEN 1
		WHEN mode IN ('soloShowdown', 'loneStar') AND showdown_rank > 4 THEN 0
		WHEN mode IN ('duoShowdown') AND showdown_rank <= 2 THEN 1
		WHEN mode IN ('duoShowdown') AND showdown_rank > 2 THEN 0 ELSE win END) AS wins, 
	COUNT(brawler) AS matches_played
INTO individual_aggs_mid
FROM records
WHERE trophies >= 300
AND trophies < 550
GROUP BY map, mode, brawler, player_id;

SELECT mode, map, brawler, player_id,
	SUM(CASE WHEN mode IN ('soloShowdown', 'loneStar') AND showdown_rank <= 4 THEN 1
		WHEN mode IN ('soloShowdown', 'loneStar') AND showdown_rank > 4 THEN 0
		WHEN mode IN ('duoShowdown') AND showdown_rank <= 2 THEN 1
		WHEN mode IN ('duoShowdown') AND showdown_rank > 2 THEN 0 ELSE win END) AS wins, 
	COUNT(brawler) AS matches_played
INTO individual_aggs_low
FROM records
WHERE trophies < 300
GROUP BY map, mode, brawler, player_id;

/*Create create multi-indexes for faster querying.*/
CREATE INDEX pop_idx_high ON population_aggs_high(mode,map,brawler);
CREATE INDEX pop_idx_mid ON population_aggs_mid(mode,map,brawler);
CREATE INDEX pop_idx_low ON population_aggs_low(mode,map,brawler);
CREATE INDEX ind_idx_high ON individual_aggs_high(mode,map,brawler,player_id);
CREATE INDEX ind_idx_mid ON individual_aggs_mid(mode,map,brawler,player_id);
CREATE INDEX ind_idx_low ON individual_aggs_low(mode,map,brawler,player_id);

ANALYZE;