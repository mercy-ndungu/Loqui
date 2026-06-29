-- Loqui auth schema (run in Supabase SQL editor)

create extension if not exists "pgcrypto";

create table if not exists public.users (
    id uuid primary key default gen_random_uuid(),
    email text not null unique,
    password_hash text not null,
    full_name text not null,
    created_at timestamptz not null default now()
);

create index if not exists users_email_idx on public.users (email);

create table if not exists public.user_profiles (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null unique references public.users (id) on delete cascade,
    presentation_goal text not null,
    target_audience text not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists user_profiles_user_id_idx on public.user_profiles (user_id);

alter table public.users enable row level security;
alter table public.user_profiles enable row level security;

-- Presentations and related coaching artifacts

create table if not exists public.presentations (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users (id) on delete cascade,
    title text not null,
    presentation_type text not null check (
        presentation_type in (
            'pitch', 'interview', 'networking', 'general', 'improv', 'random_topic'
        )
    ),
    storage_path text,
    pdf_url text,
    challenge_metadata jsonb,
    created_at timestamptz not null default now()
);

create index if not exists presentations_user_id_idx on public.presentations (user_id);

create table if not exists public.recordings (
    id uuid primary key default gen_random_uuid(),
    presentation_id uuid not null references public.presentations (id) on delete cascade,
    storage_path text not null,
    video_url text not null,
    duration_seconds integer,
    transcription_encrypted text not null default '',
    created_at timestamptz not null default now()
);

create index if not exists recordings_presentation_id_idx on public.recordings (presentation_id);

create table if not exists public.feedback (
    id uuid primary key default gen_random_uuid(),
    recording_id uuid not null references public.recordings (id) on delete cascade,
    feedback_json jsonb not null default '{}',
    created_at timestamptz not null default now()
);

create index if not exists feedback_recording_id_idx on public.feedback (recording_id);

-- Challenge practice sessions (improv pictures, random topics)

create table if not exists public.challenges (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references public.users (id) on delete cascade,
    challenge_type text not null check (challenge_type in ('improv', 'topic')),
    title text not null,
    topic_or_images text,
    metadata jsonb not null default '{}',
    storage_path text,
    video_url text,
    duration_seconds integer,
    transcription_encrypted text not null default '',
    created_at timestamptz not null default now(),
    completed_at timestamptz
);

create index if not exists challenges_user_id_idx on public.challenges (user_id);
create index if not exists challenges_completed_at_idx on public.challenges (completed_at);

-- Feedback can link to a presentation recording OR a challenge session
alter table public.feedback
    alter column recording_id drop not null;

alter table public.feedback
    add column if not exists challenge_id uuid references public.challenges (id) on delete cascade;

create index if not exists feedback_challenge_id_idx on public.feedback (challenge_id);

alter table public.challenges enable row level security;
alter table public.presentations enable row level security;
alter table public.recordings enable row level security;
alter table public.feedback enable row level security;

-- Create Storage buckets in the Supabase dashboard (private):
--   presentations
--   recordings

-- Migration: allow anonymous challenge sessions (public topic preview)
-- alter table public.challenges alter column user_id drop not null;

-- Migration for challenges (run in Supabase SQL editor):
-- create table public.challenges (...);  -- see full definition above
-- alter table public.feedback alter column recording_id drop not null;
-- alter table public.feedback add column if not exists challenge_id uuid
--     references public.challenges (id) on delete cascade;

-- Migration for existing deployments (run in Supabase SQL editor):
-- alter table public.presentations alter column storage_path drop not null;
-- alter table public.presentations alter column pdf_url drop not null;
-- alter table public.presentations add column if not exists challenge_metadata jsonb;
-- alter table public.presentations drop constraint if exists presentations_presentation_type_check;
-- alter table public.presentations add constraint presentations_presentation_type_check
--     check (presentation_type in (
--         'pitch', 'interview', 'networking', 'general', 'improv', 'random_topic'
--     ));

-- Migration for existing feedback tables:
-- alter table public.feedback add column if not exists feedback_json jsonb not null default '{}';
-- update public.feedback set feedback_json = content where feedback_json = '{}' and content is not null;
-- alter table public.feedback drop column if exists content;
-- alter table public.recordings add column if not exists video_url text;
-- alter table public.recordings add column if not exists transcription_encrypted text not null default '';
-- update public.recordings set video_url = storage_path where video_url is null and storage_path is not null;

-- Backend uses the service_role key, which bypasses RLS for server-side access.
alter table public.presentations alter column storage_path drop not null;
alter table public.presentations alter column pdf_url drop not null;
alter table public.presentations add column if not exists challenge_metadata jsonb;
alter table public.presentations drop constraint if exists presentations_presentation_type_check;
alter table public.presentations add constraint presentations_presentation_type_check
    check (presentation_type in (
        'pitch', 'interview', 'networking', 'general', 'improv', 'random_topic'
    ));



    create table if not exists public.challenges (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users (id) on delete cascade,
    challenge_type text not null check (challenge_type in ('improv', 'topic')),
    title text not null,
    topic_or_images text,
    metadata jsonb not null default '{}',
    storage_path text,
    video_url text,
    duration_seconds integer,
    transcription_encrypted text not null default '',
    created_at timestamptz not null default now(),
    completed_at timestamptz
);

alter table public.feedback alter column recording_id drop not null;
alter table public.feedback add column if not exists challenge_id uuid
    references public.challenges (id) on delete cascade;

alter table public.challenges alter column user_id drop not null;