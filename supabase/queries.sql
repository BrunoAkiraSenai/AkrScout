-- =============================================================================
-- AKR Scout - Common Queries
-- Use these queries in Supabase SQL Editor or your application.
-- =============================================================================

-- LIST ACTIVE JOBS (paginated)
select * from vw_jobs
where status = 'active'
order by scraped_at desc
limit 20
offset 0;

-- FILTER BY REMOTE + SENIORITY
select * from vw_jobs
where status = 'active'
  and remote = true
  and seniority = 'senior'
order by posted_at desc;

-- SEARCH BY TITLE
select * from vw_jobs
where status = 'active'
  and title ilike '%react%'
order by posted_at desc;

-- TOP 10 SKILLS
select name, slug, demand_count
from vw_top_skills
limit 10;

-- TOP 10 COMPANIES
select name, job_count, avg_salary_min, avg_salary_max
from vw_top_companies
limit 10;

-- REMOTE WORK STATS
select * from vw_remote_stats;

-- SALARY DISTRIBUTION
select * from vw_salary_by_seniority;

-- USER FAVORITES (authenticated)
select
  f.id as favorite_id,
  f.created_at as favorited_at,
  j.id as job_id,
  j.title,
  c.name as company_name
from favorites f
join jobs j on j.id = f.job_id
join companies c on c.id = j.company_id
where f.user_id = auth.uid()
order by f.created_at desc;

-- TOGGLE FAVORITE (function)
select fn_toggle_favorite('job-uuid-here');

-- UPSERT JOB FROM SCRAPER
select fn_upsert_job(
  p_company_id      => 'company-uuid',
  p_title           => 'Senior Frontend Engineer',
  p_description     => 'We are looking for...',
  p_location        => 'San Francisco, CA',
  p_remote          => true,
  p_seniority       => 'senior',
  p_employment_type => 'full_time',
  p_salary_min      => 150000,
  p_salary_max      => 200000,
  p_currency        => 'USD',
  p_job_url         => 'https://example.com/job/123',
  p_source          => 'linkedin',
  p_posted_at       => now() - interval '2 days'
);

-- ATTACH SKILLS TO A JOB
select fn_set_job_skills(
  p_job_id    => 'job-uuid',
  p_skill_ids => array[
    (select id from skills where slug = 'react'),
    (select id from skills where slug = 'typescript'),
    (select id from skills where slug = 'tailwind-css')
  ]::uuid[]
);

-- GENERATE ANALYTICS SNAPSHOT
insert into analytics_snapshots (
  top_skills,
  top_companies,
  remote_percentage,
  avg_salary_range,
  total_jobs
)
select
  (select jsonb_agg(jsonb_build_object('name', name, 'count', demand_count))
   from vw_top_skills limit 10),
  (select jsonb_agg(jsonb_build_object('name', name, 'count', job_count))
   from vw_top_companies limit 10),
  (select remote_percentage from vw_remote_stats),
  (select jsonb_build_object(
    'min', min(salary_min),
    'max', max(salary_max),
    'avg', round(avg((salary_min + salary_max) / 2))
   ) from jobs where status = 'active' and salary_min is not null),
  (select count(*) from jobs where status = 'active');

-- CLEANUP EXPIRED JOBS (run daily)
update jobs
set status = 'expired'
where status = 'active'
  and posted_at < now() - interval '90 days';
