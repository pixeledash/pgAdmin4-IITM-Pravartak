-- Trigger: trig_test_$%{}[]()&*^!@"'`\/#

-- DROP TRIGGER IF EXISTS "trig_test_$%{}[]()&*^!@""'`\/#" ON public.tablefortrigger;

CREATE TRIGGER "trig_test_$%{}[]()&*^!@""'`\/#"
    BEFORE INSERT
    ON public.tablefortrigger
    FOR EACH ROW
    EXECUTE PROCEDURE public."Trig1_$%{}[]()&*^!@""'`\/#"();

COMMENT ON TRIGGER "trig_test_$%{}[]()&*^!@""'`\/#" ON public.tablefortrigger
    IS 'test comment';
