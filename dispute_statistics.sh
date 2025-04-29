read -p "Number of days to check (90): " days
days=${days:-90}
read -p "Number of days to exclude (2): " days_exclude
days_exclude=${days_exclude:-2}

total_days=$((days + days_exclude))

container_name='sql-lndmn'
db_user='postgres'
db_name='postgres'

echo "Successful orders without dispute"
docker exec -t $container_name psql -U $db_user -d $db_name -c  "
    SELECT COUNT(*), SUM(o.last_satoshis), MAX(o.last_satoshis), MIN(o.last_satoshis), AVG(o.last_satoshis), STDDEV_SAMP(o.last_satoshis) FROM api_order as o
    WHERE o.status = 14 AND o.is_disputed = False AND o.created_at > NOW() - INTERVAL '$total_days days' AND o.created_at < NOW() - INTERVAL '$days_exclude days'"

echo "Successful orders in dispute"
docker exec -t $container_name psql -U $db_user -d $db_name -c  "
    SELECT COUNT(*), SUM(o.last_satoshis), MAX(o.last_satoshis), MIN(o.last_satoshis), AVG(o.last_satoshis), STDDEV_SAMP(o.last_satoshis) FROM api_order as o
    WHERE o.status = 14 AND o.is_disputed = True AND o.created_at > NOW() - INTERVAL '$total_days days' AND o.created_at < NOW() - INTERVAL '$days_exclude days'"

echo "Orders punished in dispute"
docker exec -t $container_name psql -U $db_user -d $db_name -c  "
    SELECT COUNT(*), SUM(o.last_satoshis), MAX(o.last_satoshis), MIN(o.last_satoshis), AVG(o.last_satoshis), STDDEV_SAMP(o.last_satoshis) FROM api_order as o
    WHERE (o.status = 17 OR o.status = 18) AND o.is_disputed = True AND o.created_at > NOW() - INTERVAL '$total_days days' AND o.created_at < NOW() - INTERVAL '$days_exclude days'"

echo "Collaborative cancellations in dispute"
docker exec -t $container_name psql -U $db_user -d $db_name -c  "
    SELECT COUNT(*), SUM(o.last_satoshis), MAX(o.last_satoshis), MIN(o.last_satoshis), AVG(o.last_satoshis), STDDEV_SAMP(o.last_satoshis) FROM api_order as o
    WHERE o.status = 12 AND o.is_disputed = True AND o.created_at > NOW() - INTERVAL '$total_days days' AND o.created_at < NOW() - INTERVAL '$days_exclude days'"

echo "Collaborative cancellations without dispute"
docker exec -t $container_name psql -U $db_user -d $db_name -c  "
    SELECT COUNT(*), SUM(o.last_satoshis), MAX(o.last_satoshis), MIN(o.last_satoshis), AVG(o.last_satoshis), STDDEV_SAMP(o.last_satoshis) FROM api_order as o
    WHERE o.status = 12 AND o.is_disputed = False AND o.created_at > NOW() - INTERVAL '$total_days days' AND o.created_at < NOW() - INTERVAL '$days_exclude days'"

echo "Onchain payments"
docker exec -t $container_name psql -U $db_user -d $db_name -c  "
    SELECT COUNT(*), SUM(sent_satoshis), MAX(sent_satoshis), MIN(sent_satoshis), AVG(sent_satoshis), STDDEV_SAMP(sent_satoshis) FROM api_onchainpayment
    WHERE status = 2 AND created_at > NOW() - INTERVAL '$total_days days' AND created_at < NOW() - INTERVAL '$days_exclude days'"

docker exec -t $container_name psql -U $db_user -d $db_name -c  "
    SELECT DATE(NOW() - INTERVAL '$total_days days') AS starting_day, DATE(NOW() - INTERVAL '$days_exclude days') AS final_day;"
