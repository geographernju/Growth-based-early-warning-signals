library(dplR)
library(tools)

dir.create("D:/data/Processed data/Detrending", recursive = TRUE, showWarnings = FALSE)
dir.create("D:/data/Processed data/mistake", recursive = TRUE, showWarnings = FALSE)

rwl_files <- c("D:/data/HDY2.rwl")

for (file_path in rwl_files) {
  tryCatch({
    file_name <- basename(file_path)
    csv_name <- file_path_sans_ext(file_name)
    
    lines <- readLines(file_path)
    if (length(lines) <= 3) stop("Insufficient file data: no content after the first three lines")
    temp_file <- tempfile(fileext = ".rwl")
    writeLines(lines[-c(1:3)], temp_file)
    rwl_data <- read.rwl(temp_file)
    unlink(temp_file)
    
    rwi_negexp <- detrend(rwl_data, method = "ModNegExp")
    rwi_spline <- detrend(rwl_data, method = "Spline", nyrs = 30)
    rwi_agedep <- detrend(rwl_data, method = "AgeDepSpline")
    
    crn_negexp <- chron(rwi_negexp, prefix = "")
    crn_spline <- chron(rwi_spline, prefix = "")
    crn_agedep <- chron(rwi_agedep, prefix = "")
    
    if (any(is.na(crn_negexp$std)) || any(is.na(crn_spline$std)) || any(is.na(crn_agedep$std))) stop("Chronology construction failed")
    
    years <- as.numeric(rownames(crn_agedep))
    
    df_negexp <- data.frame(year = years, ModNegExp = crn_negexp$std, samp.depth = crn_negexp$samp.depth)
    df_spline <- data.frame(year = years, Spline = crn_spline$std)
    df_agedep <- data.frame(year = years, AgeDepSpline = crn_agedep$std)
    
    ## RCS
    rw <- as.matrix(rwl_data)
    ages <- apply(rw, 2, function(x){ idx <- which(!is.na(x)); a <- rep(NA_real_, length(x)); if(length(idx)>0) a[idx] <- seq_along(idx); a })
    max_age <- suppressWarnings(max(ages, na.rm = TRUE))
    rc <- sapply(seq_len(max_age), function(a) mean(rw[ages == a], na.rm = TRUE))
    rc[!is.finite(rc) | rc <= 0] <- NA_real_
    rwi_rcs <- rw
    for(j in seq_len(ncol(rw))){
      aj <- ages[,j]
      ok <- !is.na(rw[,j]) & !is.na(aj) & !is.na(rc[aj])
      rwi_rcs[ok,j] <- rw[ok,j] / rc[aj[ok]]
      rwi_rcs[!ok,j] <- NA_real_
    }
    rwi_rcs <- as.data.frame(rwi_rcs); rownames(rwi_rcs) <- rownames(rwl_data); colnames(rwi_rcs) <- colnames(rwl_data)
    crn_rcs <- chron(rwi_rcs, prefix = "")
    df_rcs <- data.frame(year = as.numeric(rownames(crn_rcs)), RCS = crn_rcs$std)
    
    ## SFRCS (iterates from RCS; default maximum: 8 iterations, tol=1e-4)
    make_chron_vec <- function(ch){ y <- as.numeric(rownames(ch)); v <- ch$std; yrs_all <- as.numeric(rownames(rwl_data)); out <- rep(NA_real_, length(yrs_all)); names(out) <- yrs_all; ii <- match(y, yrs_all); out[ii] <- v; out }
    chron_prev <- make_chron_vec(crn_rcs)
    max_iter <- 8; tol <- 1e-4
    for(it in seq_len(max_iter)){
      Cmat <- matrix(chron_prev, nrow = nrow(rw), ncol = ncol(rw))
      sf <- rw; ok <- is.finite(rw) & is.finite(Cmat) & Cmat > 0
      sf[ok] <- rw[ok] / Cmat[ok]; sf[!ok] <- NA_real_
      rc_sf <- sapply(seq_len(max_age), function(a) mean(sf[ages == a], na.rm = TRUE))
      rc_sf[!is.finite(rc_sf) | rc_sf <= 0] <- NA_real_
      rwi_sfrcs <- rw
      for(j in seq_len(ncol(rw))){
        aj <- ages[,j]
        ok2 <- !is.na(rw[,j]) & !is.na(aj) & !is.na(rc_sf[aj])
        rwi_sfrcs[ok2,j] <- rw[ok2,j] / rc_sf[aj[ok2]]
        rwi_sfrcs[!ok2,j] <- NA_real_
      }
      rwi_sfrcs_df <- as.data.frame(rwi_sfrcs); rownames(rwi_sfrcs_df) <- rownames(rwl_data); colnames(rwi_sfrcs_df) <- colnames(rwl_data)
      crn_sfrcs_now <- chron(rwi_sfrcs_df, prefix = "")
      chron_now <- make_chron_vec(crn_sfrcs_now)
      diffv <- max(abs(chron_now - chron_prev), na.rm = TRUE)
      chron_prev <- chron_now
      if (!is.finite(diffv) || diffv < tol) break
    }
    crn_sfrcs <- crn_sfrcs_now
    df_sfrcs <- data.frame(year = as.numeric(rownames(crn_sfrcs)), SFRCS = crn_sfrcs$std)
    
    merged_crn <- Reduce(function(x, y) merge(x, y, by = "year", all = TRUE),
                         list(df_negexp, df_spline, df_agedep))
    merged_crn <- merge(merged_crn, df_rcs, by = "year", all = TRUE)
    merged_crn <- merge(merged_crn, df_sfrcs, by = "year", all = TRUE)
    
    eps_vec <- rep(NA, nrow(rwi_agedep))
    rwi_years <- as.numeric(rownames(rwi_agedep))
    for (i in seq_along(rwi_years)) {
      values <- rwi_agedep[i, ]
      valid_samples <- which(!is.na(values))
      n <- length(valid_samples)
      if (n >= 2) {
        mat <- rwi_agedep[, valid_samples]
        cor_mat <- suppressWarnings(cor(mat, use = "pairwise.complete.obs"))
        r_vals <- cor_mat[lower.tri(cor_mat)]
        rbar <- mean(r_vals, na.rm = TRUE)
        eps_vec[i] <- (n * rbar) / (n * rbar + (1 - rbar))
      }
    }
    eps_df <- data.frame(year = rwi_years, EPS = eps_vec)
    merged_crn <- merge(merged_crn, eps_df, by = "year", all = TRUE)
    write.csv(merged_crn, file = paste0("D:/data/Processed data/Detrending/", csv_name, ".csv"), row.names = FALSE)
    message("✅ Successfully processed: ", file_name)
    
  }, error = function(e) {
    file.copy(file_path, paste0("D:/data/Processed data/mistake/", basename(file_path)), overwrite = TRUE)
    message("❌ Failed: ", basename(file_path), "; error message: ", e$message)
  })
}
