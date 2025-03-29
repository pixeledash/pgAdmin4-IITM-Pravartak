-- Publication: test_publication_create

-- DROP PUBLICATION IF EXISTS test_publication_create;

CREATE PUBLICATION test_publication_create
    FOR TABLE public.test_table_publication (emp_id, name)
    WITH (publish = 'insert, update, delete, truncate', publish_via_partition_root = false);