--
-- PostgreSQL database dump
--

-- Dumped from database version 15.8
-- Dumped by pg_dump version 15.13 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: processor_chains; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.processor_chains (
    chain_id text NOT NULL,
    description text,
    chain_json jsonb,
    version text,
    updated_at timestamp without time zone DEFAULT now(),
    enabled boolean DEFAULT true NOT NULL,
    type text DEFAULT 'runnable'::text,
    tenant_id text DEFAULT 'default'::text NOT NULL
);


--
-- Name: task_manifest; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.task_manifest (
    task text NOT NULL,
    phrase_examples jsonb,
    required_fields jsonb,
    processor_chain_id text,
    output_type text,
    enabled boolean DEFAULT true,
    metadata jsonb DEFAULT '{}'::jsonb,
    embedding public.vector(1536),
    tenant_id text DEFAULT 'default'::text NOT NULL,
    title text
);


--
-- Name: templates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.templates (
    template_id text NOT NULL,
    tenant_id text NOT NULL,
    path text NOT NULL,
    type text,
    created_at timestamp with time zone DEFAULT now(),
    filename text
);


--
-- Name: wizard_drafts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.wizard_drafts (
    draft_id uuid NOT NULL,
    tenant_id text NOT NULL,
    goal text,
    template_id text,
    required_fields jsonb DEFAULT '[]'::jsonb,
    step integer DEFAULT 1,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    chain_json jsonb,
    trigger_phrases jsonb DEFAULT '[]'::jsonb,
    published_at timestamp with time zone,
    goal_description text,
    title text
);


--
-- PostgreSQL database dump complete
--

