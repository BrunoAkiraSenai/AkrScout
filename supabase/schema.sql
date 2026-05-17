-- =============================================================================
-- AKR Scout - Database Schema
-- Supabase PostgreSQL
-- =============================================================================
-- This file contains the complete database schema for AKR Scout.
-- Run this in the Supabase SQL Editor to initialize the database.
-- =============================================================================

-- 1. EXTENSIONS --------------------------------------------------------------

create extension if not exists "pgcrypto";

-- 2. TABLES -------------------------------------------------------------------

-- 2.1 companies
-- Stores information about companies that post job listings.
create table if not exists companies (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  website     text,
  logo_url    text,
  created_at  timestamptz not null default now()
);

comment on table companies is 'Companies that post job listings';
comment on column companies.name is 'Company display name';
comment on column companies.website is 'Company official website URL';
comment on column companies.logo_url is 'Company logo image URL';

-- 2.2 jobs
-- Core table storing all job listings discovered through scraping.
create table if not exists jobs (
  id              uuid primary key default gen_random_uuid(),
  company_id      uuid not null references companies(id) on delete cascade,
  title           text not null,
  description     text,
  location        text,
  remote          boolean not null default false,
  seniority       text,
  employment_type text,
  salary_min      numeric,
  salary_max      numeric,
  currency        text not null default 'USD',
  job_url         text,
  source          text,
  status          text not null default 'active',
  content_hash    text,
  posted_at       timestamptz,
  scraped_at      timestamptz not null default now(),
  created_at      timestamptz not null default now(),

  -- Validate employment_type
  constraint chk_employment_type check (
    employment_type is null or employment_type in (
      'full_time', 'part_time', 'contract', 'internship', 'temporary'
    )
  ),

  -- Validate seniority
  constraint chk_seniority check (
    seniority is null or seniority in (
      'junior', 'mid', 'senior', 'lead', 'principal'
    )
  ),

  -- Validate status
  constraint chk_status check (
    status in ('active', 'expired', 'filled', 'archived')
  ),

  -- Validate salary range
  constraint chk_salary_range check (
    salary_min is null or salary_max is null or salary_min <= salary_max
  )
);

comment on table jobs is 'Job listings discovered through scraping';
comment on column jobs.title is 'Job title (e.g., Senior Frontend Engineer)';
comment on column jobs.description is 'Full job description HTML or markdown';
comment on column jobs.location is 'Human-readable location (e.g., San Francisco, CA)';
comment on column jobs.remote is 'Whether the position is remote-eligible';
comment on column jobs.seniority is 'Experience level: junior, mid, senior, lead, principal';
comment on column jobs.employment_type is 'Employment type: full_time, part_time, contract, etc.';
comment on column jobs.salary_min is 'Minimum salary for the position';
comment on column jobs.salary_max is 'Maximum salary for the position';
comment on column jobs.currency is 'Salary currency (ISO 4217 code)';
comment on column jobs.job_url is 'Original URL of the job listing (used for dedup)';
comment on column jobs.source is 'Platform where the job was found (linkedin, indeed, etc.)';
comment on column jobs.status is 'Current status: active, expired, filled, archived';
comment on column jobs.content_hash is 'MD5 hash of title+company_id+location for cross-source dedup';
comment on column jobs.posted_at is 'Original posting date from source';
comment on column jobs.scraped_at is 'When this job was last scraped';

-- 2.3 skills
-- Normalized skill tags used across job listings.
create table if not exists skills (
  id          uuid primary key default gen_random_uuid(),
  name        text not null,
  slug        text not null,
  created_at  timestamptz not null default now()
);

comment on table skills is 'Normalized skill tags (e.g., React, Python, AWS)';
comment on column skills.name is 'Display name of the skill';
comment on column skills.slug is 'URL-friendly identifier for the skill';

-- 2.4 job_skills
-- Many-to-many relationship between jobs and skills.
create table if not exists job_skills (
  id          uuid primary key default gen_random_uuid(),
  job_id      uuid not null references jobs(id) on delete cascade,
  skill_id    uuid not null references skills(id) on delete cascade
);

comment on table job_skills is 'Maps skills to job listings (many-to-many)';

-- 2.5 favorites
-- User-specific saved/bookmarked job listings.
create table if not exists favorites (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references auth.users(id) on delete cascade,
  job_id      uuid not null references jobs(id) on delete cascade,
  created_at  timestamptz not null default now()
);

comment on table favorites is 'Jobs saved/bookmarked by users';

-- 2.6 analytics_snapshots
-- Pre-computed analytics snapshots for dashboard performance.
create table if not exists analytics_snapshots (
  id                uuid primary key default gen_random_uuid(),
  top_skills        jsonb,
  top_companies     jsonb,
  remote_percentage numeric,
  avg_salary_range  jsonb,
  total_jobs        integer,
  snapshot_date     date not null default current_date,
  generated_at      timestamptz not null default now()
);

comment on table analytics_snapshots is 'Pre-computed analytics for dashboard (one row per day)';

-- 3. UNIQUE CONSTRAINTS & DEDUPLICATION --------------------------------------

-- Companies: prevent duplicate company names (case-insensitive)
create unique index idx_companies_name_lower on companies (lower(name));

-- Jobs: prevent duplicate URLs (only when URL exists)
create unique index idx_jobs_url on jobs (job_url) where job_url is not null;

-- Jobs: prevent cross-source duplicates via content hash
create unique index idx_jobs_content_hash on jobs (content_hash) where content_hash is not null;

-- Skills: enforce unique slug
create unique index idx_skills_slug on skills (slug);

-- Skills: prevent duplicate names (case-insensitive)
create unique index idx_skills_name_lower on skills (lower(name));

-- Job skills: prevent duplicate mapping
create unique index idx_job_skills_unique on job_skills (job_id, skill_id);

-- Favorites: one favorite per user per job
create unique index idx_favorites_unique on favorites (user_id, job_id);

-- 4. PERFORMANCE INDEXES -----------------------------------------------------

-- Jobs: filter by company
create index idx_jobs_company_id on jobs (company_id);

-- Jobs: full-text search on title
create index idx_jobs_title on jobs (title);

-- Jobs: filter by remote status
create index idx_jobs_remote on jobs (remote) where remote = true;

-- Jobs: filter by seniority
create index idx_jobs_seniority on jobs (seniority);

-- Jobs: filter by employment type
create index idx_jobs_employment_type on jobs (employment_type);

-- Jobs: sort and filter by date
create index idx_jobs_posted_at on jobs (posted_at desc);
create index idx_jobs_scraped_at on jobs (scraped_at desc);

-- Jobs: filter by source platform
create index idx_jobs_source on jobs (source);

-- Jobs: filter by active status
create index idx_jobs_status on jobs (status) where status = 'active';

-- Jobs: composite index for common listing queries
create index idx_jobs_listing on jobs (status, posted_at desc, remote, seniority)
  where status = 'active';

-- Favorites: find all jobs for a user
create index idx_favorites_user_id on favorites (user_id);

-- Favorites: find who favorited a job
create index idx_favorites_job_id on favorites (job_id);

-- Skills: search by name
create index idx_skills_name on skills (name);

-- Analytics: lookup by date
create index idx_analytics_snapshots_date on analytics_snapshots (snapshot_date desc);

-- 5. ROW LEVEL SECURITY ------------------------------------------------------

-- 5.1 companies
alter table companies enable row level security;

create policy "Companies are publicly readable"
  on companies for select
  to public
  using (true);

create policy "Companies are manageable by service role only"
  on companies for insert
  to service_role
  with check (true);

create policy "Companies are manageable by service role only"
  on companies for update
  to service_role
  using (true);

create policy "Companies are manageable by service role only"
  on companies for delete
  to service_role
  using (true);

-- 5.2 jobs
alter table jobs enable row level security;

create policy "Jobs are publicly readable"
  on jobs for select
  to public
  using (true);

create policy "Jobs are manageable by service role only"
  on jobs for insert
  to service_role
  with check (true);

create policy "Jobs are manageable by service role only"
  on jobs for update
  to service_role
  using (true);

create policy "Jobs are manageable by service role only"
  on jobs for delete
  to service_role
  using (true);

-- 5.3 skills
alter table skills enable row level security;

create policy "Skills are publicly readable"
  on skills for select
  to public
  using (true);

create policy "Skills are manageable by service role only"
  on skills for insert
  to service_role
  with check (true);

create policy "Skills are manageable by service role only"
  on skills for update
  to service_role
  using (true);

create policy "Skills are manageable by service role only"
  on skills for delete
  to service_role
  using (true);

-- 5.4 job_skills
alter table job_skills enable row level security;

create policy "Job skills are publicly readable"
  on job_skills for select
  to public
  using (true);

create policy "Job skills are manageable by service role only"
  on job_skills for insert
  to service_role
  with check (true);

create policy "Job skills are manageable by service role only"
  on job_skills for update
  to service_role
  using (true);

create policy "Job skills are manageable by service role only"
  on job_skills for delete
  to service_role
  using (true);

-- 5.5 favorites
alter table favorites enable row level security;

create policy "Users can view their own favorites"
  on favorites for select
  to authenticated
  using (auth.uid() = user_id);

create policy "Users can create their own favorites"
  on favorites for insert
  to authenticated
  with check (auth.uid() = user_id);

create policy "Users can delete their own favorites"
  on favorites for delete
  to authenticated
  using (auth.uid() = user_id);

-- 5.6 analytics_snapshots
alter table analytics_snapshots enable row level security;

create policy "Analytics snapshots are publicly readable"
  on analytics_snapshots for select
  to public
  using (true);

create policy "Analytics snapshots are manageable by service role only"
  on analytics_snapshots for insert
  to service_role
  with check (true);

create policy "Analytics snapshots are manageable by service role only"
  on analytics_snapshots for update
  to service_role
  using (true);

create policy "Analytics snapshots are manageable by service role only"
  on analytics_snapshots for delete
  to service_role
  using (true);

-- 6. FUNCTIONS ---------------------------------------------------------------

-- 6.1 Generate content hash for job deduplication
-- Creates an MD5 hash from title, company_id, and location.
-- This detects the same job posted across different sources.
create or replace function fn_generate_job_hash(
  p_title      text,
  p_company_id uuid,
  p_location   text
) returns text
language sql
immutable
as $$
  select encode(
    digest(
      lower(trim(p_title)) || '::' || p_company_id::text || '::' || lower(coalesce(p_location, '')),
      'md5'
    ),
    'hex'
  );
$$;

comment on function fn_generate_job_hash is 'Generates a consistent hash for job deduplication';

-- 6.2 Toggle favorite
-- Adds or removes a favorite for the current user.
create or replace function fn_toggle_favorite(p_job_id uuid)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_exists boolean;
begin
  select exists(
    select 1 from public.favorites
    where user_id = auth.uid() and job_id = p_job_id
  ) into v_exists;

  if v_exists then
    delete from public.favorites
    where user_id = auth.uid() and job_id = p_job_id;
    return false;
  else
    insert into public.favorites (user_id, job_id)
    values (auth.uid(), p_job_id);
    return true;
  end if;
end;
$$;

comment on function fn_toggle_favorite is 'Toggles a favorite for the authenticated user. Returns the new state (true=favorited).';

-- 6.3 Batch upsert jobs (for scraping pipeline)
-- Inserts or updates jobs in bulk, handling deduplication via job_url or content_hash.
create or replace function fn_upsert_job(
  p_company_id    uuid,
  p_title         text,
  p_description   text       default null,
  p_location      text       default null,
  p_remote        boolean    default false,
  p_seniority     text       default null,
  p_employment_type text     default null,
  p_salary_min    numeric    default null,
  p_salary_max    numeric    default null,
  p_currency      text       default 'USD',
  p_job_url       text       default null,
  p_source        text       default null,
  p_posted_at     timestamptz default null
) returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_job_id    uuid;
  v_content_hash text;
begin
  v_content_hash := fn_generate_job_hash(p_title, p_company_id, p_location);

  insert into public.jobs (
    company_id, title, description, location, remote,
    seniority, employment_type, salary_min, salary_max, currency,
    job_url, source, posted_at, scraped_at, content_hash
  ) values (
    p_company_id, p_title, p_description, p_location, p_remote,
    p_seniority, p_employment_type, p_salary_min, p_salary_max, p_currency,
    p_job_url, p_source, p_posted_at, now(), v_content_hash
  )
  on conflict (content_hash) where content_hash is not null
  do update set
    description     = coalesce(excluded.description, jobs.description),
    salary_min      = coalesce(excluded.salary_min, jobs.salary_min),
    salary_max      = coalesce(excluded.salary_max, jobs.salary_max),
    job_url         = coalesce(excluded.job_url, jobs.job_url),
    scraped_at      = now(),
    status          = 'active'
  returning id into v_job_id;

  return v_job_id;
end;
$$;

comment on function fn_upsert_job is 'Creates or updates a job with automatic deduplication via content_hash. Returns the job ID.';

-- 6.4 Attach skills to a job
-- Replaces all skills for a given job in a single operation.
create or replace function fn_set_job_skills(
  p_job_id    uuid,
  p_skill_ids uuid[]
) returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
  delete from public.job_skills where job_id = p_job_id;

  insert into public.job_skills (job_id, skill_id)
  select p_job_id, unnest(p_skill_ids);
end;
$$;

comment on function fn_set_job_skills is 'Replaces all skills attached to a job with the provided skill IDs';

-- 7. VIEWS -------------------------------------------------------------------

-- 7.1 Jobs with company and skills (main listing view)
-- Note: favorites are handled via separate queries to respect RLS.
create or replace view vw_jobs
with (security_invoker = true)
as
select
  j.id,
  j.title,
  j.description,
  j.location,
  j.remote,
  j.seniority,
  j.employment_type,
  j.salary_min,
  j.salary_max,
  j.currency,
  j.job_url,
  j.source,
  j.posted_at,
  j.scraped_at,
  j.status,
  c.id as company_id,
  c.name as company_name,
  c.logo_url as company_logo,
  c.website as company_website,
  coalesce(
    jsonb_agg(
      jsonb_build_object('id', s.id, 'name', s.name, 'slug', s.slug)
    ) filter (where s.id is not null),
    '[]'::jsonb
  ) as skills
from jobs j
join companies c on c.id = j.company_id
left join job_skills js on js.job_id = j.id
left join skills s on s.id = js.skill_id
group by j.id, c.id, c.name, c.logo_url, c.website;

comment on view vw_jobs is 'Complete job listing with company details and skills';

-- 7.2 Latest active jobs (optimized for dashboard feed)
create or replace view vw_recent_jobs
with (security_invoker = true)
as
select *
from vw_jobs
where status = 'active'
order by scraped_at desc;

comment on view vw_recent_jobs is 'Recently scraped active jobs for the dashboard feed';

-- 7.3 Top skills by demand
create or replace view vw_top_skills
with (security_invoker = true)
as
select
  s.id,
  s.name,
  s.slug,
  count(js.job_id) as demand_count,
  rank() over (order by count(js.job_id) desc) as rank
from skills s
join job_skills js on js.skill_id = s.id
join jobs j on j.id = js.job_id and j.status = 'active'
group by s.id, s.name, s.slug
order by demand_count desc;

comment on view vw_top_skills is 'Skills ranked by number of active job listings';

-- 7.4 Top companies by job count
create or replace view vw_top_companies
with (security_invoker = true)
as
select
  c.id,
  c.name,
  c.logo_url,
  c.website,
  count(j.id) as job_count,
  round(avg(j.salary_min))::numeric as avg_salary_min,
  round(avg(j.salary_max))::numeric as avg_salary_max
from companies c
join jobs j on j.company_id = c.id and j.status = 'active'
group by c.id, c.name, c.logo_url, c.website
order by job_count desc;

comment on view vw_top_companies is 'Companies ranked by number of active job listings';

-- 7.5 Remote work statistics
create or replace view vw_remote_stats
with (security_invoker = true)
as
select
  count(*) as total_jobs,
  count(*) filter (where remote = true) as remote_jobs,
  round(
    100.0 * count(*) filter (where remote = true) / nullif(count(*), 0),
    1
  ) as remote_percentage,
  count(*) filter (where remote = true and status = 'active') as active_remote_jobs,
  count(*) filter (where remote = false and status = 'active') as active_onsite_jobs
from jobs;

comment on view vw_remote_stats is 'Aggregated remote vs onsite work statistics';

-- 7.6 Salary distribution by seniority
create or replace view vw_salary_by_seniority
with (security_invoker = true)
as
select
  seniority,
  count(*) as job_count,
  round(avg(salary_min))::numeric as avg_salary_min,
  round(avg(salary_max))::numeric as avg_salary_max,
  min(salary_min) as min_salary,
  max(salary_max) as max_salary
from jobs
where status = 'active'
  and seniority is not null
  and salary_min is not null
group by seniority
order by avg_salary_max desc;

comment on view vw_salary_by_seniority is 'Salary distribution broken down by seniority level';

-- 8. SEED DATA ---------------------------------------------------------------

-- Insert seed skills (commonly found in tech job listings)
insert into skills (name, slug) values
  ('JavaScript', 'javascript'),
  ('TypeScript', 'typescript'),
  ('React', 'react'),
  ('Node.js', 'nodejs'),
  ('Python', 'python'),
  ('Go', 'go'),
  ('Rust', 'rust'),
  ('AWS', 'aws'),
  ('Docker', 'docker'),
  ('Kubernetes', 'kubernetes'),
  ('PostgreSQL', 'postgresql'),
  ('MongoDB', 'mongodb'),
  ('GraphQL', 'graphql'),
  ('Next.js', 'nextjs'),
  ('Tailwind CSS', 'tailwind-css'),
  ('Vue.js', 'vuejs'),
  ('Angular', 'angular'),
  ('Ruby', 'ruby'),
  ('Java', 'java'),
  ('C#', 'csharp'),
  ('Swift', 'swift'),
  ('Kotlin', 'kotlin'),
  ('Flutter', 'flutter'),
  ('React Native', 'react-native'),
  ('Terraform', 'terraform'),
  ('CI/CD', 'cicd'),
  ('Machine Learning', 'machine-learning'),
  ('Data Science', 'data-science'),
  ('System Design', 'system-design'),
  ('Microservices', 'microservices')
on conflict (slug) do nothing;

-- Insert seed companies (well-known tech employers)
do $$
begin
  if not exists (select 1 from companies where lower(name) in (
    'google', 'meta', 'apple', 'amazon', 'netflix', 'microsoft', 'spotify', 'stripe', 'shopify', 'airbnb'
  )) then
    insert into companies (name, website) values
      ('Google', 'https://careers.google.com'),
      ('Meta', 'https://www.metacareers.com'),
      ('Apple', 'https://jobs.apple.com'),
      ('Amazon', 'https://www.amazon.jobs'),
      ('Netflix', 'https://jobs.netflix.com'),
      ('Microsoft', 'https://careers.microsoft.com'),
      ('Spotify', 'https://www.lifeatspotify.com'),
      ('Stripe', 'https://stripe.com/jobs'),
      ('Shopify', 'https://www.shopify.com/careers'),
      ('Airbnb', 'https://www.airbnb.com/careers');
  end if;
end;
$$;
